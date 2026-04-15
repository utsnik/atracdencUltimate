/*
 * This file is part of AtracDEnc.
 *
 * AtracDEnc is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * AtracDEnc is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with AtracDEnc; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
 */

#include "atrac3denc.h"
#include "transient_detector.h"
#include "atrac/atrac_psy_common.h"
#include <assert.h>
#include <algorithm>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <cmath>
namespace NAtracDEnc {

using namespace NMDCT;
using namespace NAtrac3;
using std::vector;

namespace {
struct TMlFrameFeatures {
    float BandEnergy[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    float AvgFlatness = 0.0f;
    float HfRatio = 0.0f;
    float TransientScore = 0.0f;
};

static std::ofstream* gFeatureLog = nullptr;
static int gFeatureFrameIdx = 0;

static TMlFrameFeatures ExtractMlFrameFeatures(const std::vector<float>& specs) {
    TMlFrameFeatures f;
    static constexpr float kEps = 1e-12f;
    float totalEnergy = 0.0f;
    float maxAbs = 0.0f;
    float meanAbs = 0.0f;
    for (size_t i = 0; i < specs.size(); ++i) {
        const float v = specs[i];
        const float a = std::abs(v);
        const float e = v * v;
        totalEnergy += e;
        meanAbs += a;
        maxAbs = std::max(maxAbs, a);
        const size_t band = std::min<size_t>(3, i / 256);
        f.BandEnergy[band] += e;
    }
    meanAbs /= std::max<size_t>(1, specs.size());
    f.TransientScore = maxAbs / (meanAbs + kEps);

    float flatAccum = 0.0f;
    for (size_t band = 0; band < 4; ++band) {
        const size_t start = band * 256;
        const size_t end = start + 256;
        float lin = 0.0f;
        float logSum = 0.0f;
        for (size_t i = start; i < end; ++i) {
            const float e = specs[i] * specs[i] + kEps;
            lin += e;
            logSum += std::log(e);
        }
        const float am = lin / 256.0f;
        const float gm = std::exp(logSum / 256.0f);
        flatAccum += gm / (am + kEps);
    }
    f.AvgFlatness = flatAccum / 4.0f;
    f.HfRatio = (f.BandEnergy[2] + f.BandEnergy[3]) / (totalEnergy + kEps);
    if (gFeatureLog && gFeatureLog->is_open()) {
        *gFeatureLog << gFeatureFrameIdx++ << ','
                     << f.BandEnergy[0] << ',' << f.BandEnergy[1] << ','
                     << f.BandEnergy[2] << ',' << f.BandEnergy[3] << ','
                     << f.TransientScore << ',' << f.AvgFlatness << ','
                     << f.HfRatio << '\n';
    }
    return f;
}

static TAtrac3BitStreamWriter::TMlHints PredictMlHints(const TMlFrameFeatures& f, bool enableMlHints) {
    TAtrac3BitStreamWriter::TMlHints h;
    if (!enableMlHints) {
        return h;
    }

    // Placeholder policy until a trained model is integrated:
    // map stable perceptual indicators into bounded decision hints.
    h.Confidence = 0.75f;
    h.HfNoiseBias = std::max(-1.0f, std::min(1.0f, (f.HfRatio - 0.24f) * 4.0f));
    h.GainBias = std::max(-1.0f, std::min(1.0f, (f.TransientScore - 4.5f) * 0.22f));
    h.TonalBias = std::max(-1.0f, std::min(1.0f, (0.50f - f.AvgFlatness) * 2.0f));
    h.BfuBudgetBias = std::max(-1.0f, std::min(1.0f, 0.55f * h.HfNoiseBias + 0.25f * h.GainBias));
    return h;
}

static uint8_t BfuBandFromIndex(uint8_t bfu) {
    for (uint8_t band = 0; band < TAtrac3Data::NumQMF; ++band) {
        if (bfu >= TAtrac3Data::BlocksPerBand[band] && bfu < TAtrac3Data::BlocksPerBand[band + 1]) {
            return band;
        }
    }
    return TAtrac3Data::NumQMF - 1;
}

static void BuildSimpleTonalBlocks(const std::vector<float>& specs,
                                   TScaler<TAtrac3Data>& scaler,
                                   std::vector<TAtrac3Data::TTonalVal>* tonalVals,
                                   std::vector<TTonalBlock>* tonalBlocks) {
    struct TCandidate {
        uint16_t Pos = 0;
        uint8_t Bfu = 0;
        float Peak = 0.0f;
    };

    std::vector<TCandidate> cands;
    cands.reserve(32);
    for (uint8_t bfu = 0; bfu < TAtrac3Data::MaxBfus; ++bfu) {
        const uint16_t first = TAtrac3Data::BlockSizeTab[bfu];
        const uint16_t last = TAtrac3Data::BlockSizeTab[bfu + 1];
        if (last <= first + 2) {
            continue;
        }

        float sumAbs = 0.0f;
        float bestPeak = 0.0f;
        uint16_t bestPos = first;
        for (uint16_t i = first + 1; i + 1 < last; ++i) {
            const float a = std::abs(specs[i]);
            sumAbs += a;
            if (a > std::abs(specs[i - 1]) && a >= std::abs(specs[i + 1]) && a > bestPeak) {
                bestPeak = a;
                bestPos = i;
            }
        }
        const float meanAbs = sumAbs / std::max<uint16_t>(1, last - first - 2);
        if (bestPeak < 0.015f) {
            continue;
        }
        if (bestPeak / (meanAbs + 1e-9f) < 3.5f) {
            continue;
        }
        cands.push_back({bestPos, bfu, bestPeak});
    }

    std::sort(cands.begin(), cands.end(), [](const TCandidate& a, const TCandidate& b) {
        return a.Peak > b.Peak;
    });

    static constexpr uint8_t kMaxTonalsPerBand = 7;
    static constexpr size_t kMaxTonalsTotal = 24;
    uint8_t bandCount[TAtrac3Data::NumQMF] = {0, 0, 0, 0};
    std::vector<TCandidate> selected;
    selected.reserve(std::min(kMaxTonalsTotal, cands.size()));
    for (const auto& c : cands) {
        if (selected.size() >= kMaxTonalsTotal) {
            break;
        }
        const uint8_t band = BfuBandFromIndex(c.Bfu);
        if (bandCount[band] >= kMaxTonalsPerBand) {
            continue;
        }
        selected.push_back(c);
        bandCount[band]++;
    }

    tonalVals->clear();
    tonalBlocks->clear();
    tonalVals->reserve(selected.size());
    tonalBlocks->reserve(selected.size());

    for (const auto& c : selected) {
        tonalVals->push_back({c.Pos, c.Peak, c.Bfu});
    }
    for (size_t i = 0; i < tonalVals->size(); ++i) {
        const auto& t = (*tonalVals)[i];
        const uint16_t first = TAtrac3Data::BlockSizeTab[t.Bfu];
        const uint16_t last = TAtrac3Data::BlockSizeTab[t.Bfu + 1];
        const uint16_t s = std::max<uint16_t>(first, static_cast<uint16_t>(t.Pos > 2 ? t.Pos - 2 : t.Pos));
        const uint16_t e = std::min<uint16_t>(last, static_cast<uint16_t>(t.Pos + 3));
        const uint16_t len = std::max<uint16_t>(1, static_cast<uint16_t>(e - s));
        auto scaled = scaler.Scale(&specs[s], len);
        tonalBlocks->emplace_back(&(*tonalVals)[i], std::move(scaled));
    }
}

static float Clamp01(float x) {
    return std::max(0.0f, std::min(1.0f, x));
}

static uint16_t ClampGainLevel(uint16_t level) {
    return static_cast<uint16_t>(std::max<uint16_t>(0, std::min<uint16_t>(15, level)));
}

static bool InFrameWindow(uint64_t frameNum, uint32_t startFrame, uint32_t maxFrames) {
    if (frameNum < startFrame) {
        return false;
    }
    if (maxFrames == 0) {
        return true;
    }
    const uint64_t endFrameExclusive = static_cast<uint64_t>(startFrame) + static_cast<uint64_t>(maxFrames);
    return frameNum < endFrameExclusive;
}

static void YamlWriteFloatSeq(std::ostream& out, const float* data, size_t len, size_t precision) {
    out << std::fixed << std::setprecision((int)precision) << "[";
    for (size_t i = 0; i < len; ++i) {
        if (i) {
            out << ", ";
        }
        out << data[i];
    }
    out << "]";
}

static void YamlWriteFloatSeq(std::ostream& out, const std::vector<float>& data, size_t precision) {
    YamlWriteFloatSeq(out, data.data(), data.size(), precision);
}
} // namespace

TSpectralUpsamplerResult TSpectralUpsampler::Process(const float* in) const {
    TSpectralUpsamplerResult result;
    static constexpr size_t kSrcLen = 640;
    static constexpr size_t kUpsampleFactor = 8;
    result.signal.resize(kSrcLen * kUpsampleFactor);

    const float alpha = std::max(0.05f, std::min(0.95f, HighpassCutoff / std::max(1.0f, InputSampleRate)));
    float totalEnergy = 0.0f;
    float hfEnergy = 0.0f;
    for (size_t i = 0; i < kSrcLen; ++i) {
        const float prev = (i == 0) ? in[i] : in[i - 1];
        const float cur = in[i];
        const float next = (i + 1 < kSrcLen) ? in[i + 1] : cur;
        for (size_t phase = 0; phase < kUpsampleFactor; ++phase) {
            const float t = static_cast<float>(phase + 1) / static_cast<float>(kUpsampleFactor);
            const float interp = cur + (next - cur) * t;
            const float baseline = cur * (1.0f - alpha) + prev * alpha;
            const float hp = interp - baseline;
            result.signal[i * kUpsampleFactor + phase] = hp;
            totalEnergy += interp * interp;
            hfEnergy += hp * hp;
        }
    }

    result.highFreqRatio = hfEnergy / std::max(totalEnergy, 1e-9f);
    return result;
}

static std::vector<TGainCurvePoint> CalcCurve(const std::vector<float>& gain,
                                              TBandCurveContext& ctx,
                                              float nextLevel,
                                              float minScore,
                                              bool enableContinuityMode,
                                              bool enableGainExp,
                                              bool enableGainExp2,
                                              bool* continuityClampedOut,
                                              bool* weakTransientSuppressedOut,
                                              float* targetPrevOut,
                                              float* targetCurOut,
                                              uint8_t* firstLevelPrevOut,
                                              uint8_t* firstLevelCurOut,
                                              std::ostream* yamlLog,
                                              const std::vector<float>* gainLow,
                                              const std::vector<float>* gainHigh) {
    std::vector<TGainCurvePoint> points;
    if (continuityClampedOut) {
        *continuityClampedOut = false;
    }
    if (weakTransientSuppressedOut) {
        *weakTransientSuppressedOut = false;
    }
    const bool gainExperimentMode = enableGainExp || enableGainExp2;
    const float prevTarget = ctx.LastTarget;
    const uint8_t prevFirstLevel = ctx.LastHadCurve ? ctx.LastFirstLevel : 4;
    if (targetPrevOut) {
        *targetPrevOut = prevTarget;
    }
    if (firstLevelPrevOut) {
        *firstLevelPrevOut = prevFirstLevel;
    }
    if (gain.empty()) {
        ctx.LastTarget = std::max(1e-6f, nextLevel);
        ctx.LastLevel = 0.0f;
        ctx.LastHadCurve = false;
        ctx.LastFirstLevel = 4;
        ctx.LastCurveRun = 0;
        if (targetCurOut) {
            *targetCurOut = ctx.LastTarget;
        }
        if (firstLevelCurOut) {
            *firstLevelCurOut = 4;
        }
        return points;
    }

    const size_t tailStart = gain.size() > 8 ? gain.size() - 8 : 0;
    float tailMean = 0.0f;
    for (size_t i = tailStart; i < gain.size(); ++i) {
        tailMean += gain[i];
    }
    tailMean /= static_cast<float>(gain.size() - tailStart);
    float target = std::max(1e-6f, 0.75f * tailMean + 0.25f * std::max(nextLevel, 1e-6f));
    if (enableContinuityMode && prevTarget > 1e-6f && ctx.LastHadCurve) {
        const float targetDelta = std::abs(std::log(std::max(target, 1e-6f) / std::max(prevTarget, 1e-6f)));
        if (targetDelta < 0.14f) {
            target = 0.75f * prevTarget + 0.25f * target;
            if (continuityClampedOut) {
                *continuityClampedOut = true;
            }
        }
    }

    float maxGain = 0.0f;
    size_t maxPos = 0;
    for (size_t i = 0; i < gain.size(); ++i) {
        if (gain[i] > maxGain) {
            maxGain = gain[i];
            maxPos = i;
        }
    }

    const float attackScore = maxGain / std::max(target, 1e-6f);
    ctx.LastTarget = target;
    ctx.LastLevel = maxGain;
    if (targetCurOut) {
        *targetCurOut = target;
    }
    if (attackScore < minScore) {
        ctx.LastHadCurve = false;
        ctx.LastFirstLevel = 4;
        ctx.LastCurveRun = 0;
        if (firstLevelCurOut) {
            *firstLevelCurOut = 4;
        }
        return points;
    }

    const float localLow = (gainLow && maxPos < gainLow->size()) ? (*gainLow)[maxPos] : target;
    const float localHigh = (gainHigh && maxPos < gainHigh->size()) ? (*gainHigh)[maxPos] : maxGain;
    const float toneWeightedScore = attackScore * (1.0f + 0.2f * Clamp01((localHigh - localLow) / std::max(localHigh, 1e-6f)));

    if (enableContinuityMode || gainExperimentMode) {
        const float sustainRatio = nextLevel / std::max(maxGain, 1e-6f);
        const float marginalAttackLimit = enableGainExp2 ? minScore * 1.26f
                                     : (enableGainExp ? minScore * 1.18f : minScore * 1.10f);
        const float sustainLimit = enableGainExp2 ? 0.34f
                              : (enableGainExp ? 0.42f : 0.30f);
        bool weakIsolatedTransient = attackScore < marginalAttackLimit && sustainRatio < sustainLimit;
        if (!weakIsolatedTransient && gainExperimentMode) {
            size_t attackWidth = 0;
            const float widthThreshold = maxGain * (enableGainExp2 ? 0.70f : 0.65f);
            for (float sample : gain) {
                if (sample >= widthThreshold) {
                    ++attackWidth;
                }
            }
            weakIsolatedTransient = attackWidth <= (enableGainExp2 ? 1 : 2)
                                 && attackScore < minScore * (enableGainExp2 ? 1.34f : 1.28f)
                                 && sustainRatio < (enableGainExp2 ? 0.46f : 0.55f);
        }
        if (weakIsolatedTransient) {
            ctx.LastHadCurve = false;
            ctx.LastFirstLevel = 4;
            ctx.LastCurveRun = 0;
            if (weakTransientSuppressedOut) {
                *weakTransientSuppressedOut = true;
            }
            if (firstLevelCurOut) {
                *firstLevelCurOut = 4;
            }
            return points;
        }
    }

    const uint16_t level = ClampGainLevel(RelationToIdx(std::max(1.0f, toneWeightedScore)));
    const uint16_t location = static_cast<uint16_t>(std::min<size_t>(31, maxPos > 0 ? maxPos - 1 : 0));
    points.push_back({level, location});

    // Sony FUN_00440d20-style greedy multi-point selection.
    // After placing the primary peak, iteratively find the next strongest
    // attack above a secondary threshold, up to 6 additional points.
    // Sony selects top-N from ~40 candidates via iterative max-scan;
    // this replicates that strategy over the 32 subframe gain array.
    {
        std::vector<float> residual(gain);
        // Zero out primary peak and neighbors to prevent clustering
        static constexpr size_t kNeighborRadius = 2;
        const size_t zeroStart = (maxPos >= kNeighborRadius) ? maxPos - kNeighborRadius : 0;
        const size_t zeroEnd   = std::min(gain.size() - 1, maxPos + kNeighborRadius);
        for (size_t k = zeroStart; k <= zeroEnd; ++k) residual[k] = 0.0f;

        // Secondary threshold: ~65% of primary trigger.
        const float secondaryThresh = target * minScore * 0.65f;
        // Sony caps at 7 gain points total; reserve one slot for the primary.
        // at3tool decoder supports max 6 gain points per band (empirically verified).
        // MaxGainPointsNum=8 is the array bound; 7+ points cause 0x1000105 decode error.
        const size_t maxExtra = std::min<size_t>(5,
            static_cast<size_t>(TAtrac3Data::SubbandInfo::MaxGainPointsNum) - 2);

        for (size_t extra = 0; extra < maxExtra; ++extra) {
            float nextMax = 0.0f;
            size_t nextPos = 0;
            for (size_t i = 0; i < residual.size(); ++i) {
                if (residual[i] > nextMax) { nextMax = residual[i]; nextPos = i; }
            }
            if (nextMax <= 0.0f || nextMax < secondaryThresh) break;

            const uint16_t nextLevel = ClampGainLevel(
                RelationToIdx(nextMax / std::max(target, 1e-6f)));
            const uint16_t nextLoc = static_cast<uint16_t>(
                std::min<size_t>(31, nextPos > 0 ? nextPos - 1 : 0));
            points.push_back({nextLevel, nextLoc});

            const size_t nzStart = (nextPos >= kNeighborRadius) ? nextPos - kNeighborRadius : 0;
            const size_t nzEnd   = std::min(residual.size() - 1, nextPos + kNeighborRadius);
            for (size_t k = nzStart; k <= nzEnd; ++k) residual[k] = 0.0f;
        }

        // Gain encoder requires points in ascending location order
        std::sort(points.begin(), points.end(),
                  [](const TGainCurvePoint& a, const TGainCurvePoint& b) {
                      return a.Location < b.Location;
                  });
    }

    if (yamlLog) {
        *yamlLog << std::fixed << std::setprecision(5)
                 << "        curve_target: " << target << "\n"
                 << "        curve_attack_score: " << attackScore << "\n";
    }

    if (enableContinuityMode && !points.empty()) {
        const int prevLevel = prevFirstLevel;
        const int curLevel = points[0].Level;
        const int delta = curLevel - prevLevel;
        // Stability mode should smooth obvious one-frame jumps, but keep enough
        // headroom for strong attacks (to avoid "underwater" vocal regressions).
        const int kMaxFirstLevelDelta = gainExperimentMode ? 1 : 3;
        const bool sustainedContext = ctx.LastHadCurve && ctx.LastCurveRun >= 1;
        const bool strongAttack = attackScore >= minScore * 2.2f;
        const bool singlePointCurve = points.size() == 1;
        // Preserve intentional downward moves to level 1; clamping those tends to
        // smear vocal attacks in long-form material. We still clamp hard drops to 0.
        const bool allowDownToOne = !gainExperimentMode && (delta < 0) && (curLevel >= 1);
        if (sustainedContext && !singlePointCurve && !strongAttack && !allowDownToOne && std::abs(delta) > kMaxFirstLevelDelta) {
            points[0].Level = ClampGainLevel(static_cast<uint16_t>(prevLevel + (delta > 0 ? kMaxFirstLevelDelta : -kMaxFirstLevelDelta)));
            if (continuityClampedOut) {
                *continuityClampedOut = true;
            }
        }
    }

    ctx.LastHadCurve = !points.empty();
    ctx.LastFirstLevel = points.empty() ? 4 : points[0].Level;
    ctx.LastCurveRun = points.empty() ? 0 : static_cast<uint8_t>(std::min<int>(255, static_cast<int>(ctx.LastCurveRun) + 1));
    if (firstLevelCurOut) {
        *firstLevelCurOut = ctx.LastFirstLevel;
    }

    return points;
}

void TAtrac3MDCT::Mdct(float specs[1024], float* bands[4], float maxLevels[4], TGainModulatorArray gainModulators)
{
    for (int band = 0; band < 4; ++band) {
        float* srcBuff = bands[band];
        float* const curSpec = &specs[band*256];
        TGainModulator modFn = gainModulators[band];
        float tmp[512];
        memcpy(&tmp[0], srcBuff, 256 * sizeof(float));
        if (modFn) {
            modFn(&tmp[0], &srcBuff[256]);
        }
        float max = 0.0;
        for (int i = 0; i < 256; i++) {
            max = std::max(max, std::abs(srcBuff[256+i]));
            srcBuff[i] = TAtrac3Data::EncodeWindow[i] * srcBuff[256+i];
            tmp[256+i] = TAtrac3Data::EncodeWindow[255-i] * srcBuff[256+i];
        }
        const vector<float>& sp = Mdct512(&tmp[0]);
        assert(sp.size() == 256);
        memcpy(curSpec, sp.data(), 256 * sizeof(float));
        if (band & 1) {
            SwapArray(curSpec, 256);
        }
        maxLevels[band] = max;
    }
}

void TAtrac3MDCT::Mdct(float specs[1024], float* bands[4], TGainModulatorArray gainModulators)
{
    static float dummy[4];
    Mdct(specs, bands, dummy, gainModulators);
}

void TAtrac3MDCT::Midct(float specs[1024], float* bands[4], TGainDemodulatorArray gainDemodulators)
{
    for (int band = 0; band < 4; ++band) {
        float* dstBuff = bands[band];
        float* curSpec = &specs[band*256];
        float* prevBuff = dstBuff + 256;
        TAtrac3GainProcessor::TGainDemodulator demodFn = gainDemodulators[band];
        if (band & 1) {
            SwapArray(curSpec, 256);
        }
        vector<float> inv  = Midct512(curSpec);
        assert(inv.size()/2 == 256);
        for (int j = 0; j < 256; ++j) {
            inv[j] *= 2 * TAtrac3Data::DecodeWindow[j];
            inv[511 - j] *= 2 * TAtrac3Data::DecodeWindow[j];
        }
        if (demodFn) {
            demodFn(dstBuff, inv.data(), prevBuff);
        } else {
            for (uint32_t j = 0; j < 256; ++j) {
                dstBuff[j] = inv[j] + prevBuff[j];
            }
        }
        memcpy(prevBuff, &inv[256], sizeof(float)*256);
    }
}

TAtrac3Encoder::TAtrac3Encoder(TCompressedOutputPtr&& oma, TAtrac3EncoderSettings&& encoderSettings)
    : Oma(std::move(oma))
    , Params(std::move(encoderSettings))
    , LoudnessCurve(CreateLoudnessCurve(TAtrac3Data::NumSamples))
    , SingleChannelElements(Params.SourceChannels)
    , Upsampler(11025.0f, 800.0f)
{
    YamlLog = Params.YamlLog;
    gFeatureLog = nullptr;
    if (!Params.FeatureLogPath.empty()) {
        static std::ofstream featureLogFile(Params.FeatureLogPath);
        featureLogFile << "frame,band0,band1,band2,band3,transient,flatness,hf_ratio\n";
        gFeatureLog = &featureLogFile;
        gFeatureFrameIdx = 0;
    }
}

TAtrac3Encoder::~TAtrac3Encoder()
{}

TAtrac3MDCT::TGainModulatorArray TAtrac3MDCT::MakeGainModulatorArray(const TAtrac3Data::SubbandInfo& si)
{
    switch (si.GetQmfNum()) {
        case 1:
        {
            return {{ GainProcessor.Modulate(si.GetGainPoints(0)), TAtrac3MDCT::TGainModulator(),
                TAtrac3MDCT::TGainModulator(), TAtrac3MDCT::TGainModulator() }};
        }
        case 2:
        {
            return {{ GainProcessor.Modulate(si.GetGainPoints(0)), GainProcessor.Modulate(si.GetGainPoints(1)),
                TAtrac3MDCT::TGainModulator(), TAtrac3MDCT::TGainModulator() }};
        }
        case 3:
        {
            return {{ GainProcessor.Modulate(si.GetGainPoints(0)), GainProcessor.Modulate(si.GetGainPoints(1)),
                GainProcessor.Modulate(si.GetGainPoints(2)), TAtrac3MDCT::TGainModulator() }};
        }
        case 4:
        {
            return {{ GainProcessor.Modulate(si.GetGainPoints(0)), GainProcessor.Modulate(si.GetGainPoints(1)),
                GainProcessor.Modulate(si.GetGainPoints(2)), GainProcessor.Modulate(si.GetGainPoints(3)) }};
        }
        default:
            assert(false);
            return {};

    }
}

float TAtrac3Encoder::LimitRel(float x)
{
    return std::min(std::max(x, TAtrac3Data::GainLevel[15]), TAtrac3Data::GainLevel[0]);
}

// Build 32 subframe-average divisors (gain levels) that Modulate would apply
// to bufNext for a given curve.
static void BuildSubframeDivisors(const std::vector<TGainCurvePoint>& pts, float outDiv[32]) {
    float sampleDiv[256];
    std::fill(sampleDiv, sampleDiv + 256, 1.0f);

    uint32_t pos = 0;
    for (size_t i = 0; i < pts.size(); ++i) {
        const uint32_t lastPos = pts[i].Location << TAtrac3Data::LocScale;
        float level = TAtrac3Data::GainLevel[pts[i].Level];
        const int incPos = ((i + 1) < pts.size() ? pts[i + 1].Level : TAtrac3Data::ExponentOffset)
                         - pts[i].Level + TAtrac3Data::GainInterpolationPosShift;
        const float gainInc = TAtrac3Data::GainInterpolation[incPos];

        for (; pos < lastPos && pos < 256; ++pos) {
            sampleDiv[pos] = level;
        }
        for (; pos < lastPos + TAtrac3Data::LocSz && pos < 256; ++pos) {
            sampleDiv[pos] = level;
            level *= gainInc;
        }
    }

    for (uint32_t sf = 0; sf < 32; ++sf) {
        float sum = 0.0f;
        for (uint32_t s = 0; s < 8; ++s)
            sum += sampleDiv[sf * 8 + s];
        outDiv[sf] = sum / 8.0f;
    }
}

// Score how well the curve keeps early-frame modulated HPF envelope near target,
// with a small penalty for abrupt divisor changes (a leakage proxy).
static float CalcCurveEarlyMismatchScore(const std::vector<float>& gain,
                                         float target,
                                         const std::vector<TGainCurvePoint>& pts) {
    if (gain.size() != 32 || target <= 1e-9f)
        return 0.0f;

    float div[32];
    BuildSubframeDivisors(pts, div);

    uint32_t maxLoc = 0;
    for (const auto& p : pts)
        maxLoc = std::max<uint32_t>(maxLoc, p.Location);
    const uint32_t evalSf = std::min<uint32_t>(32, std::max<uint32_t>(3, maxLoc + 3));

    static constexpr float kEps = 1e-9f;
    float fit = 0.0f;
    for (uint32_t sf = 0; sf < evalSf; ++sf) {
        const float mod = gain[sf] / std::max(div[sf], kEps);
        const float e = std::log2(std::max(mod, kEps) / std::max(target, kEps));
        fit += e * e;
    }
    fit /= evalSf;

    float leak = 0.0f;
    float wsum = 0.0f;
    for (uint32_t sf = 0; sf + 1 < evalSf; ++sf) {
        const float a = std::log2(std::max(div[sf], kEps));
        const float b = std::log2(std::max(div[sf + 1], kEps));
        const float d = b - a;
        const float w = 0.5f * (gain[sf] + gain[sf + 1]);
        leak += d * d * w;
        wsum += w;
    }
    if (wsum > kEps)
        leak /= wsum;

    static constexpr float kLeakWeight = 0.25f;
    return fit + kLeakWeight * leak;
}

void TAtrac3Encoder::CreateSubbandInfo(const float* upInput[4],
                                         uint32_t channel,
                                         TAtrac3Data::SubbandInfo* subbandInfo,
                                         int gainBoostPerBand[TAtrac3Data::NumQMF],
                                         bool gainContinuityClamped[TAtrac3Data::NumQMF],
                                         bool gainWeakTransientSuppressed[TAtrac3Data::NumQMF],
                                         bool hfContinuityClamped[TAtrac3Data::NumQMF],
                                         float gainTargetPrev[TAtrac3Data::NumQMF],
                                         float gainTargetCur[TAtrac3Data::NumQMF],
                                         uint8_t gainFirstLevelPrev[TAtrac3Data::NumQMF],
                                         uint8_t gainFirstLevelCur[TAtrac3Data::NumQMF])
{
    static constexpr float kLowOverlapRelax = 0.6f;      // allow softer min level when overlap is small
    static constexpr int kLevelBoostCap = 1;             // cap level boost to reduce bit starvation
    static constexpr int kScaleBoostCap = 2;             // allow extra scale boost in low-risk cases
    static constexpr float kMinScore = 1.9f;
    const bool enableGainExpMode = Params.EnableGainExp || Params.EnableGainExp2;
    const bool enableGainExp2Mode = Params.EnableGainExp2;
    const bool enableContinuityMode = Params.EnableStabilityMode || enableGainExpMode;

    // YAML: channel header (one channel per CreateSubbandInfo call)
    if (YamlLog) {
        *YamlLog << "  - channel: " << channel << "\n"
                 << "    bands:\n";
    }

    for (int band = 0; band < 4; ++band) {
        gainContinuityClamped[band] = false;
        gainWeakTransientSuppressed[band] = false;
        hfContinuityClamped[band] = false;
        gainTargetPrev[band] = CurveCtx[channel][band].LastTarget;
        gainTargetCur[band] = CurveCtx[channel][band].LastTarget;
        gainFirstLevelPrev[band] = CurveCtx[channel][band].LastHadCurve ? CurveCtx[channel][band].LastFirstLevel : 4;
        gainFirstLevelCur[band] = gainFirstLevelPrev[band];
        // YAML: band header emitted immediately so every band has an entry
        if (YamlLog) {
            *YamlLog << "      - band: " << band << "\n";
        }

        auto result = Upsampler.Process(upInput[band]);

        if (result.highFreqRatio < TSpectralUpsampler::kHighFreqThreshold) {
            if (YamlLog) {
                *YamlLog << std::fixed << std::setprecision(4)
                         << "        skip: low_hfr  # high_freq_ratio "
                         << result.highFreqRatio << " < threshold\n";
            }
            CurveCtx[channel][band].LastLevel = 0.0f;
            continue;
        }

        // Analysis region [1024..3072) = current frame upsampled (8x)
        std::vector<float> gainLow;
        std::vector<float> gainHigh;
        const auto gain = AnalyzeGain(result.signal.data() + 1024, 2048, 32, true,
                                      &gainLow, &gainHigh);

        // nextLevel from first 64-sample subframe of upsampled lookahead [3072..3072+64)
        const float nextLevel = AnalyzeGain(result.signal.data() + 3072, 64, 1, true)[0];

        // HPF-domain overlap ratio: mean HPF RMS of previous frame vs current frame.
        // This is domain-matched with gain[] (both HPF-upsampled), unlike full-band
        // overlapRatio which is inflated by bass energy that has nothing to do with
        // whether an HPF-domain transient should be protected.
        float curHpfEnergy = 0.0f;
        for (float v : gain) curHpfEnergy += v;
        curHpfEnergy /= static_cast<float>(gain.size());
        const float prevHpfEnergy = CurveCtx[channel][band].LastHpfEnergy;
        CurveCtx[channel][band].LastHpfEnergy = curHpfEnergy;
        const float hpfOverlapRatio = (curHpfEnergy > 1e-9f && prevHpfEnergy > 1e-9f)
            ? (prevHpfEnergy / curHpfEnergy) : 1.0f;

        const float* bufCur  = PcmBuffer.GetFirst(channel + band * 2);
        const float* bufNext = PcmBuffer.GetSecond(channel + band * 2);

        if (YamlLog) {
            *YamlLog << "        pcm_qmf:  # 256 raw QMF samples, non-modulated, non-windowed\n"
                     << "          ";
            YamlWriteFloatSeq(*YamlLog, bufNext, 256, 6);
            *YamlLog << "\n";
        }

        // Compute overlapRatio early so we can scale minScore accordingly.
        // High overlapRatio (prev frame >> current) means gain curves are
        // more likely to misfire; raise the threshold to suppress them.
        float overlapE = 0.0f, curE = 0.0f;
        for (int i = 0; i < 256; i++) {
            overlapE += bufCur[i] * bufCur[i];
            curE     += bufNext[i] * bufNext[i];
        }
        const float overlapRatio = overlapE / (curE + 1e-9f);

        // Dynamic min-score: raise threshold when prev HPF frame was louder.
        // Uses HPF-domain ratio so bass-heavy prev frames don't suppress real HPF transients.
        const float overlapFactor = std::min(1.5f, std::max(1.0f, hpfOverlapRatio));
        float dynamicMinScore = kMinScore * overlapFactor;
        if (Params.EnableGainExp) {
            dynamicMinScore *= 1.08f;
        }
        const bool gainTransientContext = Params.EnableStabilityMode
            && LastParityAnalysis[channel].Valid
            && LastParityAnalysis[channel].AttackRisk > 4.6f
            && LastParityAnalysis[channel].Stability < 0.78f
            && LastParityAnalysis[channel].HfRisk < 0.020f;
        if (Params.EnableStabilityMode && band <= 1) {
            // Stability lane: protect true attack runs, but keep "no curve"
            // preference when prior frame context does not support a transient lane.
            dynamicMinScore *= gainTransientContext ? 0.95f : 1.08f;
        }

        if (YamlLog) {
            *YamlLog << std::fixed << std::setprecision(4)
                     << "        high_freq_ratio: " << result.highFreqRatio << "\n"
                     << "        overlap_ratio: " << overlapRatio
                     << "  # prev_E/cur_E full-band; >1 means prev frame louder\n"
                     << "        hpf_overlap_ratio: " << hpfOverlapRatio
                     << "  # prev_HPF/cur_HPF; used for transient suppression decisions\n"
                     << "        gain_transient_context: " << (gainTransientContext ? "true" : "false") << "\n"
                     << "        dynamic_min_score: " << dynamicMinScore << "\n"
                     << "        next_level: " << nextLevel << "\n"
                     << "        gain: ";
            YamlWriteFloatSeq(*YamlLog, gain, 4);
            *YamlLog << "  # 32 subframe RMS values\n";
        }

        const float prevTarget = CurveCtx[channel][band].LastTarget;
        // Stability mode is scoped to HF bands to avoid introducing vocal wobble
        // from low-band continuity state carry-over on long-form material.
        const bool bandContinuityMode =
            enableContinuityMode && (!Params.EnableStabilityMode || band >= 2);
        auto curvePoints = CalcCurve(gain, CurveCtx[channel][band], nextLevel,
                                     dynamicMinScore, bandContinuityMode, Params.EnableGainExp, false,
                                     &gainContinuityClamped[band],
                                     &gainWeakTransientSuppressed[band],
                                     &gainTargetPrev[band],
                                     &gainTargetCur[band],
                                     &gainFirstLevelPrev[band],
                                     &gainFirstLevelCur[band],
                                     YamlLog,
                                     &gainLow, &gainHigh);
        const float curTarget = CurveCtx[channel][band].LastTarget;
        const float maxGainForGate = *std::max_element(gain.begin(), gain.end());
        const float attackScoreForGate = maxGainForGate / std::max(nextLevel, 1e-6f);
        const float sustainRatioForGate = nextLevel / std::max(maxGainForGate, 1e-6f);

        if (enableGainExpMode) {
            size_t attackWidthForGate = 0;
            const float widthThreshold = maxGainForGate * 0.70f;
            for (float sample : gain) {
                if (sample >= widthThreshold) {
                    ++attackWidthForGate;
                }
            }

            // Keep both experiment lanes narrow and isolated:
            // gain-exp: very strong short attacks in band 0 only.
            // gain-exp2: high-band (band 2) strong attacks with strict HF gating.
            const bool allowGainExpCurve = enableGainExp2Mode
                ? (band == 2 &&
                   result.highFreqRatio >= 0.62f &&
                   maxGainForGate >= 1.6e-3f &&
                   hpfOverlapRatio <= 0.30f &&
                   overlapRatio <= 0.90f &&
                   attackScoreForGate >= dynamicMinScore * 2.80f &&
                   sustainRatioForGate <= 0.22f &&
                   attackWidthForGate <= 1)
                : (band == 0 &&
                   maxGainForGate >= 1.0e-3f &&
                   hpfOverlapRatio <= 0.40f &&
                   attackScoreForGate >= dynamicMinScore * 2.20f &&
                   sustainRatioForGate <= 0.35f &&
                   attackWidthForGate <= 1);

            if (!allowGainExpCurve) {
                curvePoints.clear();
                gainWeakTransientSuppressed[band] = true;
                if (YamlLog) {
                    *YamlLog << std::fixed << std::setprecision(4)
                             << "        gain_exp_skip: narrow_gate"
                             << "  # attack_score " << attackScoreForGate
                             << ", sustain_ratio " << sustainRatioForGate
                             << ", attack_width " << attackWidthForGate << "\n";
                }
            } else if (!curvePoints.empty()) {
                if (curvePoints.size() > 1) {
                    curvePoints.resize(1);
                }
                const uint16_t maxLevel = enableGainExp2Mode ? 5 : 6;
                const uint16_t maxLocation = enableGainExp2Mode ? 4 : 6;
                curvePoints[0].Level = ClampGainLevel(std::min<uint16_t>(curvePoints[0].Level, maxLevel));
                curvePoints[0].Location = static_cast<uint16_t>(std::min<uint16_t>(curvePoints[0].Location, maxLocation));
                if (YamlLog) {
                    *YamlLog << "        gain_exp_keep: "
                             << (enableGainExp2Mode ? "hf_attack_lane\n" : "narrow_attack\n");
                }
            }
        }

        if (curvePoints.empty()) {
            if (YamlLog) {
                *YamlLog << "        skip: no_curve\n";
            }
            gainBoostPerBand[band] = 0;
            continue;
        }

        if (YamlLog) {
            *YamlLog << "        curve_raw:\n";
            for (const auto& p : curvePoints) {
                *YamlLog << "          - {level: " << p.Level
                         << ", loc: " << p.Location << "}\n";
            }
        }

        float maxGain = maxGainForGate;
        const float frameEndLevel = gain.back();
        const float ratio = maxGain / (frameEndLevel + 1e-9f);

        // Minimum signal gate: suppress curves on near-silent frames.
        // Firing on noise-floor content wastes bitrate and can produce extreme
        // Level values against a tiny target.
        // Use curvePoints.clear() (not continue) so point0 still runs for any
        // genuine cross-frame energy step at the OLA boundary.
        static constexpr float kMinSignalThreshold = 1e-4f;
        if (maxGain < kMinSignalThreshold) {
            if (YamlLog)
                *YamlLog << std::fixed << std::setprecision(6)
                         << "        skip: below_min_signal  # maxGain " << maxGain << "\n";
            gainBoostPerBand[band] = 0;
            curvePoints.clear();
        }

        // Amplifying-only curves require reliable HPF analysis.  When HFR is low
        // the HPF gain[] does not represent full-band energy: a tiny HPF transient
        // can produce level 9 (×32 amplification) on a loud full-band signal,
        // catastrophically over-inflating MDCT coefficients.
        static constexpr float kMinHfrForAmplify = 0.3f;
        if (result.highFreqRatio < kMinHfrForAmplify) {
            if (YamlLog)
                *YamlLog << "        skip: amplify_low_hfr\n";
            gainBoostPerBand[band] = 0;
            curvePoints.clear();
        }

        int levelBoost = 0;

        // Scale boost: compensate for Demodulate's `scale = GainLevel[giNext[0].Level]`.
        // When decoding frame N, scale = GainLevel[frame N+1's first gain point Level].
        // Frame N+1's CalcCurve: scaleLevel = RelationToIdx(gain.back()_N / nextLevel_{N+2}).
        // We have the full frame N+1 in the lookahead [3072..5119].  Use min(lookaheadGain)
        // as a conservative proxy for nextLevel_{N+2} (≈ quietest level reachable in N+1,
        // a lower bound on frame N+2's start level).
        int scaleBoost = 0;
        {
            static constexpr size_t kLookaheadOffset = 3072;
            const size_t outSz = result.signal.size();
            if (outSz > kLookaheadOffset + 64) {
                const uint32_t lookaheadPoints =
                    static_cast<uint32_t>(std::min<size_t>(1024, outSz - kLookaheadOffset) / 64);
                if (lookaheadPoints > 0) {
                    const auto lookaheadGain = AnalyzeGain(result.signal.data() + kLookaheadOffset,
                                                           lookaheadPoints * 64,
                                                           lookaheadPoints, true);
                    const float lookaheadMin = *std::min_element(lookaheadGain.begin(), lookaheadGain.end());
                    if (lookaheadMin > 1e-6f) {
                        const uint32_t estimatedNextScaleLevel = RelationToIdx(frameEndLevel / lookaheadMin);
                        if (estimatedNextScaleLevel < 4u)
                            scaleBoost = static_cast<int>(4u - estimatedNextScaleLevel);
                    }
                }
            }
        }

        const int scaleCap = (overlapRatio < kLowOverlapRelax) ? kScaleBoostCap : kLevelBoostCap;
        scaleBoost = std::min(scaleBoost, scaleCap);
        int totalBoost = std::min(levelBoost + scaleBoost, kLevelBoostCap);
        if (enableGainExpMode) {
            // Prevent gain-exp trials from changing allocation pressure at the same time.
            totalBoost = 0;
        }
        if (enableContinuityMode && band >= 2) {
            const int prevBoost = CurveCtx[channel][band].LastGainBoost;
            const int clampedBoost = std::max(prevBoost - 1, std::min(prevBoost + 1, totalBoost));
            if (clampedBoost != totalBoost) {
                totalBoost = clampedBoost;
                hfContinuityClamped[band] = true;
            }
        }
        CurveCtx[channel][band].LastGainBoost = totalBoost;

        if (YamlLog) {
            *YamlLog << std::fixed << std::setprecision(4)
                     << "        max_gain: " << maxGain << "\n"
                     << "        ratio: " << ratio
                     << "  # max_gain/frame_end_level, transient strength\n"
                     << "        level_boost: " << levelBoost << "\n"
                     << "        scale_boost: " << scaleBoost << "\n"
                     << "        total_boost: " << totalBoost << "\n";
        }

        // Band 3 is above ~16 kHz where pre-echo is largely inaudible.
        // Skip gain modulation there.
        if (band >= 3) {
            if (YamlLog) {
                *YamlLog << "        skip: band_ge_3"
                         << "  # inaudible HF; gain modulation disabled\n";
            }
            gainBoostPerBand[band] = 0;
            curvePoints.clear();
        }

        if (band < 3) {
            if (YamlLog)
                *YamlLog << "        gain_boost: " << totalBoost << "\n";
            gainBoostPerBand[band] = totalBoost;
        }


        // Explicit point 0: correct cross-frame energy step in the HPF domain.
        // Compare prevTarget (what the previous frame's curve was targeting, in the
        // HPF gain[] domain) against the mean HPF level of the pre-ramp zone of
        // bufNext after applying the current curve's attenuation.  Both quantities
        // are in the same filtered domain, avoiding LF-content distortion.
        if (band < 3 && !enableGainExpMode) {
            const auto curveBeforePoint0 = curvePoints;
            bool point0Changed = false;

            // hpfRmsNextMod: mean of gain[sf] / GainLevel[pts[0].Level]
            // for the subframes strictly before the first curve point's ramp start.
            // These are the only samples the curve actually attenuates at constant level.
            float hpfRmsNextMod = 0.0f;
            bool hpfRmsNextModValid = false;
            if (!curvePoints.empty() && curvePoints[0].Location > 0) {
                const uint32_t nBefore = curvePoints[0].Location;  // subSz==8 == LocScale shift
                const float divisor = TAtrac3Data::GainLevel[curvePoints[0].Level];
                float sum = 0.0f;
                for (uint32_t sf = 0; sf < nBefore; ++sf)
                    sum += gain[sf];
                hpfRmsNextMod = (sum / nBefore) / divisor;
                hpfRmsNextModValid = true;
            } else if (curvePoints.empty()) {
                float sum = 0.0f;
                for (float v : gain) sum += v;
                hpfRmsNextMod = sum / gain.size();
                hpfRmsNextModValid = true;
            }

            if (YamlLog) {
                *YamlLog << std::fixed << std::setprecision(6)
                         << "        prev_target: " << prevTarget << "\n"
                         << "        hpf_rms_next_mod: " << hpfRmsNextMod << "\n";
            }

            if (hpfRmsNextModValid && prevTarget > 1e-6f && hpfRmsNextMod > 1e-6f) {
                const uint16_t point0Level = ClampGainLevel(RelationToIdx(prevTarget / hpfRmsNextMod));
                if (YamlLog) {
                    *YamlLog << "        point0_level: " << point0Level
                             << "  # RelationToIdx(prev_target/hpf_rms_next_mod)\n";
                }
                auto it = std::find_if(curvePoints.begin(), curvePoints.end(),
                                       [](const TGainCurvePoint& p) { return p.Location == 0; });
                if (it != curvePoints.end()) {
                    if (it->Level != point0Level) {
                        it->Level = point0Level;
                        point0Changed = true;
                    }
                } else if (point0Level != 4 || !curvePoints.empty()) {
                    curvePoints.insert(curvePoints.begin(), {point0Level, 0});
                    point0Changed = true;
                }
            }

            // Guard: keep point0 only if it does not worsen local envelope fit.
            // Additional boundary protection: keep point0 if it materially
            // improves frame-boundary scale match to prevTarget/hpfRmsNextMod.
            if (point0Changed) {
                const float scoreBefore = CalcCurveEarlyMismatchScore(gain, curTarget, curveBeforePoint0);
                const float scoreAfter = CalcCurveEarlyMismatchScore(gain, curTarget, curvePoints);
                static constexpr float kPoint0WorseTol = 0.02f; // 2% tolerance
                static constexpr float kBoundaryKeepMargin = 0.20f; // 0.2 bits in log2 scale

                bool keepByBoundary = false;
                float boundaryErrBefore = 0.0f;
                float boundaryErrAfter = 0.0f;
                if (hpfRmsNextModValid && prevTarget > 1e-6f && hpfRmsNextMod > 1e-6f) {
                    const auto firstLevel = [](const std::vector<TGainCurvePoint>& pts) -> uint16_t {
                        return pts.empty() ? static_cast<uint16_t>(TAtrac3Data::ExponentOffset) : pts[0].Level;
                    };
                    const float desiredScale = LimitRel(prevTarget / hpfRmsNextMod);
                    const float scaleBefore = TAtrac3Data::GainLevel[firstLevel(curveBeforePoint0)];
                    const float scaleAfter = TAtrac3Data::GainLevel[firstLevel(curvePoints)];
                    static constexpr float kEps = 1e-9f;
                    boundaryErrBefore = std::abs(std::log2(std::max(scaleBefore, kEps) / std::max(desiredScale, kEps)));
                    boundaryErrAfter = std::abs(std::log2(std::max(scaleAfter, kEps) / std::max(desiredScale, kEps)));
                    keepByBoundary = (boundaryErrAfter + kBoundaryKeepMargin < boundaryErrBefore);
                    if (YamlLog) {
                        *YamlLog << std::fixed << std::setprecision(6)
                                 << "        point0_guard_boundary_err_before: " << boundaryErrBefore << "\n"
                                 << "        point0_guard_boundary_err_after: " << boundaryErrAfter << "\n";
                    }
                }

                if (!keepByBoundary && scoreAfter > scoreBefore * (1.0f + kPoint0WorseTol)) {
                    curvePoints = curveBeforePoint0;
                    if (YamlLog) {
                        *YamlLog << std::fixed << std::setprecision(6)
                                 << "        point0_guard: reverted  # score_after " << scoreAfter
                                 << " > score_before " << scoreBefore << "\n";
                    }
                } else if (YamlLog) {
                    *YamlLog << std::fixed << std::setprecision(6)
                             << "        point0_guard: kept  # score_before " << scoreBefore
                             << ", score_after " << scoreAfter;
                    if (keepByBoundary) {
                        *YamlLog << ", boundary_err_before " << boundaryErrBefore
                                 << ", boundary_err_after " << boundaryErrAfter;
                    }
                    *YamlLog << "\n";
                }
            }
        }
        else if (band < 3 && enableGainExpMode && YamlLog) {
            *YamlLog << "        point0_guard: skipped  # gain-exp lanes keep boundary edits off during narrow experiments\n";
        }

        // If explicit point0 has the same level as the next point, it does not
        // change modulation shape and only wastes 9 bits in the bitstream.
        if (curvePoints.size() >= 2
            && curvePoints[0].Location == 0
            && curvePoints[0].Level == curvePoints[1].Level) {
            curvePoints.erase(curvePoints.begin());
        }

        if (YamlLog) {
            *YamlLog << "        curve_final:\n";
            for (const auto& p : curvePoints) {
                *YamlLog << "          - {level: " << p.Level
                         << ", loc: " << p.Location << "}\n";
            }
        }

        std::vector<TAtrac3Data::SubbandInfo::TGainPoint> curve;
        curve.reserve(curvePoints.size());
        for (const auto& p : curvePoints) {
            curve.push_back({ClampGainLevel(p.Level), static_cast<uint16_t>(std::min<uint16_t>(31, p.Location))});
        }

        subbandInfo->AddSubbandCurve(band, std::move(curve));
    }
}

void TAtrac3Encoder::AnalyzeStereoParity()
{
    PendingStereoState = TStereoParityState();
    PendingStereoState.Valid = true;

    float stabilityAccum = 0.0f;
    for (uint32_t band = 0; band < TAtrac3Data::NumQMF; ++band) {
        const float* left = PcmBuffer.GetSecond(band * 2);
        const float* right = PcmBuffer.GetSecond(band * 2 + 1);
        float ll = 0.0f;
        float rr = 0.0f;
        float lr = 0.0f;
        float mid = 0.0f;
        float side = 0.0f;
        float transMismatch = 0.0f;
        for (uint32_t i = 0; i < 256; ++i) {
            const float l = left[i];
            const float r = right[i];
            ll += l * l;
            rr += r * r;
            lr += l * r;
            const float m = 0.5f * (l + r);
            const float s = 0.5f * (l - r);
            mid += m * m;
            side += s * s;
            transMismatch += std::abs(std::abs(l) - std::abs(r));
        }

        PendingStereoState.Coherence[band] = Clamp01(std::abs(lr) / std::sqrt(std::max(1e-9f, ll * rr)));
        PendingStereoState.SideRatio[band] = side / std::max(1e-9f, mid + side);
        PendingStereoState.TransientMismatch[band] = transMismatch / 256.0f;
        const float lastCoherence = LastStereoState.Valid ? LastStereoState.Coherence[band]
                                                          : PendingStereoState.Coherence[band];
        stabilityAccum += 1.0f - std::min(1.0f, std::abs(PendingStereoState.Coherence[band] - lastCoherence));
    }

    PendingStereoState.Stability = stabilityAccum / TAtrac3Data::NumQMF;
    LastStereoState = PendingStereoState;
}

void TAtrac3Encoder::PopulateParityAnalysis(uint32_t channel,
                                            const std::vector<float>& specs,
                                            TAtrac3BitStreamWriter::TParityFrameAnalysis* analysis)
{
    *analysis = TAtrac3BitStreamWriter::TParityFrameAnalysis();

    float bandEnergy[TAtrac3Data::NumQMF] = {};
    float totalEnergy = 0.0f;
    for (uint32_t band = 0; band < TAtrac3Data::NumQMF; ++band) {
        const size_t start = band * 256;
        const size_t end = start + 256;
        float logSum = 0.0f;
        float meanAbs = 0.0f;
        float peakAbs = 0.0f;
        for (size_t i = start; i < end; ++i) {
            const float v = specs[i];
            const float a = std::abs(v);
            const float e = v * v;
            bandEnergy[band] += e;
            meanAbs += a;
            peakAbs = std::max(peakAbs, a);
            logSum += std::log(e + 1e-9f);
        }

        totalEnergy += bandEnergy[band];
        const float am = bandEnergy[band] / 256.0f;
        const float gm = std::exp(logSum / 256.0f);
        auto& out = analysis->Bands[band];
        out.Energy = bandEnergy[band];
        out.Noisiness = Clamp01(gm / std::max(am, 1e-9f) * 1.6f);
        out.Tonality = Clamp01(1.0f - out.Noisiness);
        out.TransientScore = std::min(6.0f, peakAbs / std::max(1e-6f, meanAbs / 256.0f));
        out.DecayScore = std::min(4.0f, CurveCtx[channel][band].LastLevel / std::max(1e-6f, peakAbs));
    }

    float frameRisk = 0.0f;
    float hfRisk = 0.0f;
    float maxSibilanceRisk = 0.0f;
    float maxHfSalience = 0.0f;
    float attackRisk = 0.0f;
    float tonalRisk = 0.0f;
    float stereoRisk = 0.0f;
    float msEnergyRatio = 0.0f;
    for (uint32_t band = 0; band < TAtrac3Data::NumQMF; ++band) {
        auto& out = analysis->Bands[band];
        const float prevEnergy = (band > 0) ? bandEnergy[band - 1] : bandEnergy[band];
        const float nextEnergy = (band + 1 < TAtrac3Data::NumQMF) ? bandEnergy[band + 1] : bandEnergy[band];
        out.HfSalience = (band >= 2) ? bandEnergy[band] / std::max(1e-9f, totalEnergy) : 0.0f;
        out.MaskingThreshold = 0.42f * bandEnergy[band] + 0.22f * prevEnergy + 0.22f * nextEnergy;
        out.SibilanceRisk = (band >= 2)
            ? Clamp01(out.HfSalience * (0.55f * out.Noisiness + 0.15f * out.TransientScore))
            : 0.0f;

        if (PendingStereoState.Valid) {
            out.StereoCoherence = PendingStereoState.Coherence[band];
            out.StereoSideRatio = PendingStereoState.SideRatio[band];
            stereoRisk += (1.0f - out.StereoCoherence) * (0.6f + 0.8f * out.HfSalience);
            msEnergyRatio += out.StereoSideRatio;
        }

        const auto& prevAnalysis = LastParityAnalysis[channel];
        if (prevAnalysis.Valid) {
            const float priorEnergy = prevAnalysis.Bands[band].Energy;
            out.Stability = 1.0f - Clamp01(std::abs(std::log((bandEnergy[band] + 1e-9f) / std::max(priorEnergy, 1e-9f))));
        }

        const float bandRisk = 0.40f * out.Noisiness
                             + 0.35f * Clamp01(out.TransientScore / 4.0f)
                             + 0.25f * (1.0f - out.Stability)
                             + 0.25f * out.SibilanceRisk;
        frameRisk += bandRisk;
        hfRisk += out.SibilanceRisk;
        maxSibilanceRisk = std::max(maxSibilanceRisk, out.SibilanceRisk);
        maxHfSalience = std::max(maxHfSalience, out.HfSalience);
        attackRisk = std::max(attackRisk, out.TransientScore);
        tonalRisk = std::max(tonalRisk, out.Tonality * (0.5f + out.Energy / std::max(1e-9f, totalEnergy)));
    }

    analysis->FrameRisk = frameRisk / TAtrac3Data::NumQMF;
    analysis->StereoRisk = stereoRisk / TAtrac3Data::NumQMF;
    analysis->Stability = PendingStereoState.Valid ? PendingStereoState.Stability : 1.0f;
    analysis->HfRisk = hfRisk / TAtrac3Data::NumQMF;
    analysis->MaxSibilanceRisk = maxSibilanceRisk;
    analysis->MaxHfSalience = maxHfSalience;
    analysis->AttackRisk = attackRisk;
    analysis->TonalRisk = tonalRisk;
    analysis->MSEnergyRatio = msEnergyRatio / TAtrac3Data::NumQMF;
    analysis->Valid = Params.EnableParityAnalysis;
    LastParityAnalysis[channel] = *analysis;
}

void TAtrac3Encoder::Matrixing()
{
    for (uint32_t subband = 0; subband < 4; subband++) {
        float* pair[2] = {PcmBuffer.GetSecond(subband * 2), PcmBuffer.GetSecond(subband * 2 + 1)};
        float tmp[2];
        for (uint32_t sample = 0; sample < 256; sample++) {
            tmp[0] = pair[0][sample];
            tmp[1] = pair[1][sample];
            pair[0][sample] = (tmp[0] + tmp[1]) / 2.0;
            pair[1][sample] = (tmp[0] - tmp[1]) / 2.0;
        }
    }
}

TPCMEngine::TProcessLambda TAtrac3Encoder::GetLambda()
{
    const bool useJointStereo = Params.UseJointStereo();
    std::shared_ptr<TAtrac3BitStreamWriter> bitStreamWriter(
        new TAtrac3BitStreamWriter(Oma.get(), *Params.ConteinerParams, Params.BfuIdxConst,
                                   Params.EnableParityAnalysis, Params.EnableParitySearch,
                                   Params.EnableQualityV10, Params.EnableStabilityMode,
                                   Params.EnableStereoExp, Params.EnableStereoBalanceExp,
                                   Params.EnableGainExp, Params.EnableGainExp2,
                                   Params.EnableSmrAlloc,
                                   Params.EnableTemporalMasking,
                                   Params.StartFrame, Params.MaxFrames,
                                   Params.DecisionLog));

    struct TChannelData {
        TChannelData()
            : Specs(TAtrac3Data::NumSamples)
        {}

        vector<float> Specs;
    };

    using TData = vector<TChannelData>;
    auto buf = std::make_shared<TData>(2);

    return [this, bitStreamWriter, buf, useJointStereo](float* data, const TPCMEngine::ProcessMeta& meta) {
        using TSce = TAtrac3BitStreamWriter::TSingleChannelElement;

        // QMF-filter into the appropriate slot of LookAheadBuf:
        //   first call  → current slot  [128..383]
        //   later calls → lookahead slot [384..639]
        const int qmfOffset = LookAheadPending ? 128 : 384;
        const int monoChannel = -1; // disabled unless explicitly wired to settings
        for (uint32_t channel = 0; channel < meta.Channels; channel++) {
            float src[TAtrac3Data::NumSamples];
            if (monoChannel != -1 && channel != (uint32_t)monoChannel) {
                memset(src, 0, sizeof(float) * 1024);
            } else {
                // LP2 parity calibration: ATRAC3 path is level-sensitive and
                // at3tool-compatible decode is closest when encoder analysis
                // input is scaled by 0.25f.
                static constexpr float kAtrac3InputScale = 0.25f;
                for (size_t i = 0; i < 1024; i++) {
                    src[i] = data[i * meta.Channels  + channel] * kAtrac3InputScale;
                }
            }
            float* p[4] = {
                &LookAheadBuf[channel][0][qmfOffset],
                &LookAheadBuf[channel][1][qmfOffset],
                &LookAheadBuf[channel][2][qmfOffset],
                &LookAheadBuf[channel][3][qmfOffset]
            };
            AnalysisFilterBank[channel].Analysis(&src[0], p);
        }

        if (LookAheadPending) {
            LookAheadPending = false;
            return TPCMEngine::EProcessResult::LOOK_AHEAD;
        }

        // Copy current slot [128..383] into PcmBuffer.GetSecond for MDCT
        for (uint32_t channel = 0; channel < meta.Channels; channel++) {
            for (int b = 0; b < 4; b++) {
                memcpy(PcmBuffer.GetSecond(channel + b * 2),
                       &LookAheadBuf[channel][b][128], 256 * sizeof(float));
            }
        }

        const bool frameInWindow = InFrameWindow(FrameNum, Params.StartFrame, Params.MaxFrames);
        YamlLog = (Params.YamlLog && frameInWindow) ? Params.YamlLog : nullptr;

        if (Params.EnableParityAnalysis && frameInWindow && meta.Channels == 2) {
            AnalyzeStereoParity();
        } else {
            PendingStereoState = TStereoParityState();
        }

        if (useJointStereo && meta.Channels == 2) {
            Matrixing();
        }

        // YAML frame header: one document per frame, channels nest below.
        if (YamlLog) {
            const float timeSec = static_cast<float>(FrameNum) * TAtrac3Data::NumSamples / 44100.0f;
            *YamlLog << "---\nframe: " << FrameNum << "\n"
                     << std::fixed << std::setprecision(3)
                     << "time: " << timeSec << "  # seconds\n"
                     << "channels:\n";
        }

        for (uint32_t channel = 0; channel < meta.Channels; channel++) {
            auto& specs = (*buf)[channel].Specs;
            TSce* sce = &SingleChannelElements[channel];

            sce->SubbandInfo.Reset();
            if (!Params.NoGainControll) {
                // upInput[b] = &LookAheadBuf[channel][b][0]:
                //   [0..127]   prev tail (last 128 of previous frame)
                //   [128..383] current frame (pre-matrixing)
                //   [384..511] first 128 of lookahead frame
                // Ready to pass directly to TSpectralUpsampler::Process()
                const float* up[4] = {
                    LookAheadBuf[channel][0], LookAheadBuf[channel][1],
                    LookAheadBuf[channel][2], LookAheadBuf[channel][3]
                };
                std::fill(sce->GainBoostPerBand,
                          sce->GainBoostPerBand + TAtrac3Data::NumQMF, 0);
                CreateSubbandInfo(up, channel, &sce->SubbandInfo, sce->GainBoostPerBand,
                                  sce->GainContinuityClamped,
                                  sce->GainWeakTransientSuppressed,
                                  sce->HfContinuityClamped,
                                  sce->GainTargetPrev,
                                  sce->GainTargetCur,
                                  sce->GainFirstLevelPrev,
                                  sce->GainFirstLevelCur);
            }

            float* maxOverlapLevels = PrevPeak[channel];
            {
                float* p[4] = {
                    PcmBuffer.GetFirst(channel),   PcmBuffer.GetFirst(channel + 2),
                    PcmBuffer.GetFirst(channel + 4), PcmBuffer.GetFirst(channel + 6)
                };
                Mdct(specs.data(), p, maxOverlapLevels, MakeGainModulatorArray(sce->SubbandInfo));
            }

            float l = 0;
            for (size_t i = 0; i < specs.size(); i++) {
                float e = specs[i] * specs[i];
                l += e * LoudnessCurve[i];
            }

            sce->Loudness = l;
            const TMlFrameFeatures mlFeatures = ExtractMlFrameFeatures(specs);
            sce->MlHints = PredictMlHints(mlFeatures, Params.EnableMlHints);
            if (Params.EnableParityAnalysis && frameInWindow) {
                PopulateParityAnalysis(channel, specs, &sce->ParityAnalysis);
            } else {
                sce->ParityAnalysis = TAtrac3BitStreamWriter::TParityFrameAnalysis();
            }
            if (!Params.NoTonalComponents && !Params.EnableQualityV10) {
                BuildSimpleTonalBlocks(specs, Scaler, &sce->TonalVals, &sce->TonalBlocks);
            } else {
                sce->TonalVals.clear();
                sce->TonalBlocks.clear();
            }

            //TBlockSize for ATRAC3 - 4 subband, all are long (no short window)
            sce->ScaledBlocks = Scaler.ScaleFrame(specs, TAtrac3Data::TBlockSizeMod());
        }

        if (meta.Channels == 2 && !useJointStereo) {
            const TSce& sce0 = SingleChannelElements[0];
            const TSce& sce1 = SingleChannelElements[1];
            Loudness = TrackLoudness(Loudness, sce0.Loudness, sce1.Loudness);
        } else {
            // 1 channel or Js. In case of Js we do not use side channel to adjust loudness
            const TSce& sce0 = SingleChannelElements[0];
            Loudness = TrackLoudness(Loudness, sce0.Loudness);
        }

        if (useJointStereo && meta.Channels == 1) {
            // In case of JointStereo and one input channel (mono input) we need to construct one empty SCE to produce
            // correct bitstream
            SingleChannelElements.resize(2);
            // Set 1 subband
            SingleChannelElements[1].SubbandInfo.Info.resize(1);
        }

        bitStreamWriter->WriteSoundUnit(SingleChannelElements, Loudness / LoudFactor);

        // Advance look-ahead state: shift buffer left by 256 samples per band
        //   old [256..383] (last 128 of current) → [0..127]  new prev tail
        //   old [384..639] (lookahead)            → [128..383] new current
        //   [384..639] will be filled by the next QMF call
        for (uint32_t channel = 0; channel < meta.Channels; channel++) {
            for (int b = 0; b < 4; b++) {
                memmove(LookAheadBuf[channel][b],
                        LookAheadBuf[channel][b] + 256, 384 * sizeof(float));
            }
        }

        ++FrameNum;
        return TPCMEngine::EProcessResult::PROCESSED;
    };
}

} //namespace NAtracDEnc
