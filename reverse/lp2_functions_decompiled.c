// ============================
// RVA 0x3cdc0 -> FUN_0043cdc0

void __cdecl FUN_0043cdc0(int param_1)

{
  int iVar1;
  undefined4 *puVar2;
  
  puVar2 = (undefined4 *)(param_1 + 0x10);
  for (iVar1 = 0x40; iVar1 != 0; iVar1 = iVar1 + -1) {
    *puVar2 = 0;
    puVar2 = puVar2 + 1;
  }
  *(undefined4 *)(param_1 + 0x110) = 0;
  puVar2 = (undefined4 *)(param_1 + 0x114);
  for (iVar1 = 0x1059; iVar1 != 0; iVar1 = iVar1 + -1) {
    *puVar2 = 0;
    puVar2 = puVar2 + 1;
  }
  *(undefined4 *)(param_1 + 0x4278) = 0;
  puVar2 = (undefined4 *)(param_1 + 0x427c);
  for (iVar1 = 0x380; iVar1 != 0; iVar1 = iVar1 + -1) {
    *puVar2 = 0;
    puVar2 = puVar2 + 1;
  }
  return;
}


// ============================
// RVA 0x3ce00 -> FUN_0043ce00

int __cdecl FUN_0043ce00(int *param_1)

{
  char cVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  undefined3 extraout_var;
  
  iVar2 = FUN_0043ceb0((int)param_1);
  if (iVar2 == -0x8000) {
    return -0x8000;
  }
  iVar3 = FUN_0043d080(param_1);
  if (iVar3 == -0x8000) {
    return -0x8000;
  }
  iVar4 = FUN_0043ce80((int)param_1);
  cVar1 = FUN_0043ce60((int)param_1);
  return CONCAT31(extraout_var,cVar1) + iVar3 + iVar4 + iVar2;
}


// ============================
// RVA 0x3ceb0 -> FUN_0043ceb0

int __cdecl FUN_0043ceb0(int param_1)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  int *piVar7;
  int *piVar8;
  int *local_18;
  int local_14;
  int *local_10;
  int local_c;
  
  iVar6 = 5;
  iVar1 = *(int *)(param_1 + 0x110);
  if (iVar1 < 1) {
    if (iVar1 < 0) {
      return -0x8000;
    }
  }
  else {
    iVar6 = 7;
  }
  local_c = 0;
  if (0 < iVar1) {
    piVar7 = (int *)(param_1 + 0x118);
    do {
      if (0 < *(int *)(param_1 + 4)) {
        iVar6 = iVar6 + *(int *)(param_1 + 4);
      }
      iVar6 = iVar6 + 6;
      if (*(int *)(param_1 + 8) == 3) {
        return -0x8000;
      }
      iVar1 = piVar7[-1];
      iVar2 = *(int *)(*(int *)(*(int *)(param_1 + 0x61f4) + 0x28) + piVar7[1] * 4);
      iVar3 = FUN_0043d060(*piVar7);
      if (iVar3 == -1) {
        return -0x8000;
      }
      local_14 = 0;
      if (0 < *(int *)(param_1 + 4) << 2) {
        local_10 = piVar7 + 0x16;
        local_18 = piVar7 + 6;
        do {
          iVar4 = FUN_0043d040(local_14);
          if (iVar4 == -1) {
            return -0x8000;
          }
          if (piVar7[iVar4 + 2] != 0) {
            iVar6 = iVar6 + 3;
            iVar4 = 0;
            piVar8 = local_10;
            if (0 < *local_18) {
              do {
                iVar5 = *(int *)*piVar8;
                if (0x400 < iVar5 + iVar3) {
                  iVar3 = 0x400 - iVar5;
                }
                iVar5 = FUN_0043fdd0(iVar1 * 0x30 + iVar2,(int)((int *)*piVar8 + 2),iVar3);
                if (iVar5 == -0x8000) {
                  return -0x8000;
                }
                iVar6 = iVar6 + 0xc + iVar5;
                iVar4 = iVar4 + 1;
                piVar8 = piVar8 + 1;
              } while (iVar4 < *local_18);
            }
          }
          local_10 = local_10 + 7;
          local_14 = local_14 + 1;
          local_18 = local_18 + 1;
        } while (local_14 < *(int *)(param_1 + 4) * 4);
      }
      local_c = local_c + 1;
      piVar7 = piVar7 + 0x87;
    } while (local_c < *(int *)(param_1 + 0x110));
  }
  return iVar6;
}


// ============================
// RVA 0x3d080 -> FUN_0043d080

int __cdecl FUN_0043d080(int *param_1)

{
  int iVar1;
  int *piVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  int *piVar7;
  
  piVar2 = param_1;
  iVar6 = 0;
  iVar5 = *param_1;
  piVar7 = (int *)(iVar5 * 3 + 6);
  if (0 < iVar5) {
    do {
      if (param_1[iVar6 + 0x141f] < 1) {
        if (param_1[iVar6 + 0x141f] < 0) {
          return -0x8000;
        }
      }
      else {
        piVar7 = (int *)((int)piVar7 + 6);
      }
      iVar6 = iVar6 + 1;
    } while (iVar6 < iVar5);
  }
  iVar6 = 0;
  param_1 = piVar7;
  if (0 < iVar5) {
    do {
      iVar5 = piVar2[iVar6 + 0x141f];
      if (0 < iVar5) {
        iVar1 = *(int *)(*(int *)(piVar2[0x187d] + 0x24) + piVar2[3] * 4);
        iVar3 = FUN_0043cda0(iVar6);
        iVar4 = FUN_0043d130(iVar6);
        iVar5 = FUN_0043fdd0(iVar5 * 0x30 + iVar1,(int)(piVar2 + iVar3 + 0x145f),iVar4);
        if (iVar5 == -0x8000) {
          return -0x8000;
        }
        piVar7 = (int *)((int)param_1 + iVar5);
        param_1 = piVar7;
      }
      iVar6 = iVar6 + 1;
    } while (iVar6 < *piVar2);
  }
  return (int)piVar7;
}


// ============================
// RVA 0x3d1f0 -> FUN_0043d1f0

/* WARNING: Function: __alloca_probe replaced with injection: alloca_probe */
/* WARNING: Type propagation algorithm not settling */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int __cdecl FUN_0043d1f0(int param_1,int param_2,int *param_3,int param_4)

{
  float fVar1;
  float fVar2;
  double dVar3;
  undefined4 uVar4;
  char cVar5;
  bool bVar6;
  int iVar7;
  undefined3 extraout_var;
  undefined3 extraout_var_00;
  undefined3 extraout_var_01;
  undefined3 extraout_var_02;
  int iVar8;
  undefined3 extraout_var_03;
  int iVar9;
  int iVar10;
  int iVar11;
  uint uVar12;
  int extraout_ECX;
  int extraout_ECX_00;
  int *piVar13;
  int extraout_ECX_01;
  int extraout_ECX_02;
  int extraout_ECX_03;
  int extraout_ECX_04;
  int extraout_ECX_05;
  int extraout_ECX_06;
  int extraout_ECX_07;
  int extraout_ECX_08;
  int extraout_ECX_09;
  int extraout_ECX_10;
  int extraout_ECX_11;
  int extraout_ECX_12;
  int iVar14;
  int extraout_EDX;
  int extraout_EDX_00;
  int extraout_EDX_01;
  int extraout_EDX_02;
  int extraout_EDX_03;
  int extraout_EDX_04;
  int extraout_EDX_05;
  uint uVar15;
  float *pfVar16;
  int *piVar17;
  float *pfVar18;
  undefined4 *puVar19;
  undefined *puVar20;
  float10 fVar21;
  float10 extraout_ST0;
  float10 fVar22;
  float10 extraout_ST0_00;
  float10 extraout_ST1;
  int in_stack_ffff5754;
  int local_a85c;
  int *local_a858;
  int local_a854;
  float local_a850;
  int local_a84c;
  float local_a848;
  int *local_a844;
  float local_a840;
  int local_a83c;
  int local_a838;
  undefined *local_a834;
  int local_a830;
  float local_a82c;
  int *local_a828;
  int local_a824;
  int local_a820;
  float local_a81c [9];
  float afStack_a7f8 [23];
  int iStack_a79c;
  float local_a798 [32];
  int local_a718 [32];
  float local_a698 [32];
  int local_a618 [32];
  float local_a598 [32];
  float local_a518 [6];
  undefined4 local_a500 [31];
  float afStack_a484 [32];
  int aiStack_a404 [33];
  int aiStack_a380 [32];
  int local_a300 [31];
  int aiStack_a284 [33];
  float local_a200 [32];
  undefined4 local_a180 [32];
  uint auStack_a100 [32];
  int local_a080 [32];
  int local_a000 [1024];
  undefined1 local_9000 [4];
  int local_8ffc [4607];
  undefined1 local_4800 [18428];
  undefined4 uStack_4;
  
  uStack_4 = 0x43d1fa;
  local_a830 = param_3[0x187d];
  piVar13 = local_a000;
  for (iVar11 = 0x400; iVar11 != 0; iVar11 = iVar11 + -1) {
    *piVar13 = 0;
    piVar13 = piVar13 + 1;
  }
  iVar11 = param_3[0x1872];
  local_a828 = param_3 + 0x145f;
  uVar15 = 0;
  local_a820 = 7;
  local_a844 = (int *)0x0;
  local_a848 = 0.0;
  local_a82c = 0.0;
  local_a83c = iVar11;
  FUN_0043ec60((int)(iVar11 + (iVar11 >> 0x1f & 7U)) >> 3,local_a81c,local_a518,&local_a820);
  FUN_0043eb30(param_2,(int)local_4800,0x100);
  FUN_0043eb30(param_1,(int)local_9000,0x100);
  uVar12 = 0;
  iVar14 = 0;
  iVar7 = 0;
  do {
    if (*(int *)((int)local_8ffc + iVar14) < *(int *)((int)local_8ffc + iVar7)) {
      iVar14 = iVar7;
      uVar15 = uVar12;
    }
    iVar7 = iVar7 + 0x48;
    uVar12 = uVar12 + 1;
  } while (iVar7 < 0x4800);
  local_a834 = (undefined *)FUN_0043f110((int)local_4800);
  if ((((int)local_a834 < 1) || (param_3[0x1860] != 0)) || (*param_3 < 0x1a)) {
    cVar5 = FUN_0043ce60((int)param_3);
    iVar14 = *param_3;
    iVar7 = FUN_0043ce80((int)param_3);
    local_a85c = (((iVar11 + iVar14 * -3) - CONCAT31(extraout_var_00,cVar5)) - iVar7) + -0xd;
  }
  else {
    local_a844 = (int *)0x1;
    if ((int)uVar15 < 0xa0) {
      if (0x5f < (int)uVar15) {
        *param_3 = 0x1e;
        param_3[1] = 3;
      }
    }
    else {
      *param_3 = 0x20;
      param_3[1] = 4;
    }
    cVar5 = FUN_0043ce60((int)param_3);
    iVar14 = *param_3;
    iVar7 = FUN_0043ce80((int)param_3);
    local_a85c = (((iVar11 + iVar14 * -3) - CONCAT31(extraout_var,cVar5)) - iVar7) + -0xd;
    local_a848 = (float)FUN_0043f270(local_a85c,(int)local_a834,(0x4b0 < iVar11) + 1,uVar15,
                                     param_3[1],0x100,param_2,(int)local_4800,(int)param_3);
    if (local_a848 == -NAN) {
      return -0x8000;
    }
    local_a85c = local_a85c - (int)local_a848;
  }
  iVar11 = *param_3;
  iVar14 = param_3[1];
  local_a838 = iVar14;
  iVar7 = FUN_0043cda0(iVar11);
  local_a840 = (float)((int)(iVar7 + (iVar7 >> 0x1f & 3U)) >> 2);
  fVar1 = _DAT_0048b42c;
  if (0 < (int)local_a840) {
    piVar13 = local_8ffc;
    iVar7 = (int)local_a840;
    do {
      fVar1 = fVar1 + (float)*piVar13;
      piVar13 = piVar13 + 0x12;
      iVar7 = iVar7 + -1;
    } while (iVar7 != 0);
  }
  local_a824 = -1;
  local_a850 = 0.0;
  fVar1 = fVar1 / (float)(int)local_a840;
  if (0 < iVar14) {
    local_a858 = param_3 + 4;
    do {
      piVar13 = local_a858;
      piVar17 = (int *)&stack0xffff5754;
      for (iVar14 = 0x10; iVar14 != 0; iVar14 = iVar14 + -1) {
        *piVar17 = *piVar13;
        piVar13 = piVar13 + 1;
        piVar17 = piVar17 + 1;
      }
      bVar6 = FUN_0043e760(in_stack_ffff5754);
      if (CONCAT31(extraout_var_01,bVar6) == 1) {
        local_a824 = 0;
        goto LAB_0043d4da;
      }
      local_a850 = (float)((int)local_a850 + 1);
      local_a858 = local_a858 + 0x10;
      iVar14 = local_a838;
    } while ((int)local_a850 < local_a838);
  }
  local_a850 = 0.0;
  if (0 < iVar14) {
    local_a858 = (int *)(param_4 + 0x10);
    do {
      piVar13 = local_a858;
      puVar19 = (undefined4 *)&stack0xffff5754;
      for (iVar14 = 0x10; iVar14 != 0; iVar14 = iVar14 + -1) {
        *puVar19 = *piVar13;
        piVar13 = piVar13 + 1;
        puVar19 = puVar19 + 1;
      }
      bVar6 = FUN_0043e760(in_stack_ffff5754);
      if (CONCAT31(extraout_var_02,bVar6) == 1) {
        local_a824 = 1;
        break;
      }
      local_a850 = (float)((int)local_a850 + 1);
      local_a858 = local_a858 + 0x10;
    } while ((int)local_a850 < local_a838);
  }
LAB_0043d4da:
  local_a834 = &DAT_0048ec28;
  if (local_a844 != (int *)0x0) {
    local_a834 = &DAT_0048ec48;
  }
  if (local_a848 == 0.0) {
    local_a82c = (float)FUN_0043ec90(local_a85c,(int)local_a840,local_a838,fVar1,(int)local_4800,
                                     (int)local_9000,param_2,(int)param_3,local_a830);
  }
  local_a85c = local_a85c - (int)local_a82c;
  if (param_3[0x44] == 0) {
    local_a85c = local_a85c + 2;
  }
  FUN_0043ea90((int)local_4800,aiStack_a284 + 1,iVar11);
  FUN_0043ea90((int)local_9000,local_a618,iVar11);
  if (0 < iVar11) {
    piVar13 = local_a618;
    piVar17 = local_a080;
    for (iVar14 = iVar11; iVar14 != 0; iVar14 = iVar14 + -1) {
      *piVar17 = *piVar13;
      piVar13 = piVar13 + 1;
      piVar17 = piVar17 + 1;
    }
  }
  puVar19 = local_a500;
  for (iVar14 = 0x20; iVar14 != 0; iVar14 = iVar14 + -1) {
    *puVar19 = 1;
    puVar19 = puVar19 + 1;
  }
  puVar19 = local_a180;
  for (iVar14 = 0x20; iVar14 != 0; iVar14 = iVar14 + -1) {
    *puVar19 = 1;
    puVar19 = puVar19 + 1;
  }
  iVar14 = 0;
  pfVar16 = local_a698;
  for (iVar7 = 0x20; iVar7 != 0; iVar7 = iVar7 + -1) {
    *pfVar16 = 0.0;
    pfVar16 = pfVar16 + 1;
  }
  if (0 < iVar11) {
    do {
      fVar2 = (float)local_a618[iVar14] - fVar1;
      if (iVar14 < 8) {
        fVar2 = fVar2 * (float)_DAT_00491120;
      }
      else if (iVar14 < 0xc) {
        fVar2 = fVar2 * (float)_DAT_00491118;
      }
      else if (iVar14 < 0x10) {
        fVar2 = fVar2 * (float)_DAT_00491110;
      }
      else if (iVar14 < 0x12) {
        fVar2 = fVar2 * (float)_DAT_00491108;
      }
      else if (iVar14 < 0x1a) {
        fVar2 = fVar2 * (float)_DAT_00491100;
      }
      else if (iVar14 < 0x1c) {
        fVar2 = fVar2 * (float)_DAT_004910f8;
      }
      else if (iVar14 < 0x1e) {
        fVar2 = fVar2 * (float)_DAT_0048b440;
      }
      else {
        fVar2 = fVar2 * (float)_DAT_004910f0;
      }
      local_a81c[iVar14 + 1] = fVar2;
      iVar14 = iVar14 + 1;
    } while (iVar14 < iVar11);
  }
  if (local_a824 == -1) {
    if (local_a81c[1] < (float)_DAT_004910e0) {
      local_a81c[1] = 6.0;
    }
    iVar14 = 1;
    do {
      if (local_a81c[iVar14 + 1] < (float)_DAT_004910d8) {
        local_a81c[iVar14 + 1] = 3.0;
      }
      iVar14 = iVar14 + 1;
    } while (iVar14 < 4);
  }
  else {
    iVar14 = 0;
    do {
      uVar4 = iVar14 + 1;
      iVar14 = iVar14 + 1;
      local_a81c[iVar14] = local_a81c[uVar4] + (float)_DAT_004910e8;
    } while (iVar14 < 8);
    iVar14 = 8;
    do {
      uVar4 = iVar14 + 1;
      iVar14 = iVar14 + 1;
      local_a81c[iVar14] = local_a81c[uVar4] + (float)_DAT_00451670;
    } while (iVar14 < 0x12);
    if (local_a81c[1] < (float)_DAT_004910e0) {
      local_a81c[1] = 6.0;
    }
  }
  iVar14 = FUN_0043e7a0((int)local_a834,1,local_a81c + 1,local_a618,(int *)local_a798,iVar11,
                        local_a820);
  iVar7 = 0;
  if (0 < iVar11) {
    do {
      local_a848 = (float)aiStack_a284[iVar7 + 1];
      aiStack_a380[iVar7] = 0;
      if ((int)local_a848 < iVar14) {
        aiStack_a380[iVar7] = 1;
        local_a798[iVar7] = 0.0;
      }
      if (local_a82c == 0.0) {
        if (local_a798[iVar7] == 0.0) {
          aiStack_a380[iVar7] = 1;
        }
        if ((float)(int)local_a848 < fVar1) {
          aiStack_a380[iVar7] = 1;
        }
      }
      iVar7 = iVar7 + 1;
    } while (iVar7 < iVar11);
    if (0 < iVar11) {
      pfVar16 = local_a798;
      pfVar18 = local_a200;
      for (iVar14 = iVar11; iVar14 != 0; iVar14 = iVar14 + -1) {
        *pfVar18 = *pfVar16;
        pfVar16 = pfVar16 + 1;
        pfVar18 = pfVar18 + 1;
      }
    }
  }
  iVar14 = 0;
  if (0 < iVar11) {
    do {
      fVar21 = FUN_0043e710(aiStack_a284[iVar14 + 1]);
      if (fVar21 < (float10)_DAT_0048e8a8) {
        return -0x8000;
      }
      local_a82c = (float)((float10)DAT_0048b434 / fVar21);
      FUN_0043cda0(iVar14);
      iVar8 = FUN_0043cda0(iVar14 + 1);
      iVar7 = extraout_ECX;
      iVar14 = extraout_EDX;
      if (extraout_ECX < iVar8) {
        do {
          *(float *)(param_2 + -4 + (iVar7 + 1) * 4) = local_a82c * *(float *)(param_2 + iVar7 * 4);
          iVar8 = FUN_0043cda0(iVar14);
          iVar7 = extraout_ECX_00;
          iVar14 = extraout_EDX_00;
        } while (extraout_ECX_00 < iVar8);
      }
    } while (iVar14 < iVar11);
  }
  iVar14 = FUN_0043cda0(iVar11);
  local_a848 = (float)(iVar14 + 0x100);
  fVar1 = (float)(extraout_ST0 / (float10)(int)local_a848);
  if (extraout_ST0 / (float10)(int)local_a848 <= (float10)_DAT_004910d0) {
    if (fVar1 <= (float)_DAT_004910c8) {
      if (fVar1 <= (float)_DAT_004910c0) {
        if (fVar1 <= (float)_DAT_00491458) {
          if (fVar1 <= (float)_DAT_004910b8) {
            local_a858 = (int *)0xb;
            if (fVar1 <= (float)_DAT_004910b0) {
              local_a858 = (int *)0xc;
            }
          }
          else {
            local_a858 = (int *)0x9;
          }
        }
        else {
          local_a858 = (int *)0x7;
        }
      }
      else {
        local_a858 = (int *)0x5;
      }
    }
    else {
      local_a858 = (int *)0x3;
    }
  }
  else {
    local_a858 = (int *)0x0;
  }
  iVar14 = 0;
  if (0 < iVar11) {
    do {
      cVar5 = FUN_0043ec20(iVar14);
      fVar1 = local_a518[CONCAT31(extraout_var_03,cVar5)];
      local_a698[iVar14] = fVar1;
      if (7 < (int)fVar1) {
        local_a698[iVar14] = 9.80909e-45;
      }
      iVar14 = iVar14 + 1;
    } while (iVar14 < iVar11);
  }
  iVar14 = FUN_0043e8c0((int)local_a180,(int *)local_a798,param_2,(int)local_a828,(int)local_a718,
                        &local_a84c,iVar11,0,(int)local_a698,local_a830);
  if (iVar14 == -0x8000) {
    return -0x8000;
  }
  local_a850 = 2.0;
  local_a840 = 4.0;
  local_a854 = 0;
  do {
    if (local_a850 < (float)_DAT_0048e8a8 == (local_a850 == (float)_DAT_0048e8a8)) {
      iVar14 = 0;
      if (0 < iVar11) {
        do {
          uVar4 = iVar14 + 1;
          iVar14 = iVar14 + 1;
          afStack_a484[iVar14] = local_a850 + local_a81c[uVar4];
        } while (iVar14 < iVar11);
        goto LAB_0043da07;
      }
    }
    else {
      iVar14 = 0;
      if (0 < iVar11) {
        do {
          if (iVar14 < 1) {
            fVar1 = local_a850 * (float)_DAT_004910a8 + local_a81c[iVar14 + 1];
          }
          else if (iVar14 < 2) {
            fVar1 = local_a850 * (float)_DAT_004910a0 + local_a81c[iVar14 + 1];
          }
          else if (iVar14 < 8) {
            fVar1 = local_a850 * (float)_DAT_00491098 + local_a81c[iVar14 + 1];
          }
          else if (iVar14 < 0x12) {
            fVar1 = local_a850 * (float)_DAT_00491090 + local_a81c[iVar14 + 1];
          }
          else {
            fVar1 = local_a850 + local_a81c[iVar14 + 1];
          }
          afStack_a484[iVar14 + 1] = fVar1;
          iVar14 = iVar14 + 1;
        } while (iVar14 < iVar11);
LAB_0043da07:
        pfVar16 = local_a798;
        pfVar18 = local_a598;
        for (iVar14 = iVar11; iVar14 != 0; iVar14 = iVar14 + -1) {
          *pfVar18 = *pfVar16;
          pfVar16 = pfVar16 + 1;
          pfVar18 = pfVar18 + 1;
        }
      }
    }
    FUN_0043e7a0((int)local_a834,1,afStack_a484 + 1,local_a618,(int *)local_a798,iVar11,local_a820);
    iVar14 = 0;
    if (0 < iVar11) {
      do {
        if (((iVar14 == 0) && ((int)local_a81c[0] < 10)) && ((int)local_a798[0] < 6)) {
          local_a798[0] = 8.40779e-45;
        }
        if (local_a200[iVar14] == 0.0) {
          local_a798[iVar14] = 0.0;
        }
        iVar14 = iVar14 + 1;
      } while (iVar14 < iVar11);
    }
    iVar14 = 0;
    if (0 < iVar11) {
      do {
        local_a500[iVar14] = 0;
        if (local_a798[iVar14] != local_a598[iVar14]) {
          local_a500[iVar14] = 1;
        }
        iVar14 = iVar14 + 1;
      } while (iVar14 < iVar11);
    }
    iVar7 = FUN_0043e8c0((int)local_a500,(int *)local_a798,param_2,(int)local_a828,(int)local_a718,
                         &local_a84c,iVar11,0,(int)local_a698,local_a830);
    iVar14 = local_a830;
    if (iVar7 == -0x8000) {
      return -0x8000;
    }
    if (local_a85c < local_a84c) {
LAB_0043db21:
      local_a850 = local_a850 - local_a840;
    }
    else {
      if (5 < local_a854) break;
      if (local_a85c <= local_a84c) goto LAB_0043db21;
      local_a850 = local_a840 + local_a850;
    }
    dVar3 = _DAT_00491088;
    if (local_a854 < 7) {
      dVar3 = _DAT_00451670;
    }
    local_a840 = local_a840 * (float)dVar3;
    local_a854 = local_a854 + 1;
  } while (local_a854 < 0xf);
  local_a854 = 0;
  iVar8 = local_a84c;
  iVar7 = iVar11;
  do {
    while ((iVar7 = iVar7 + -1, -1 < iVar7 && (local_a85c < iVar8))) {
      if ((0 < (int)local_a798[iVar7]) && ((int)local_a698[iVar7] < (int)local_a858)) {
        local_a698[iVar7] = (float)((int)local_a698[iVar7] + 1);
        iVar9 = FUN_0043e8c0((int)local_a180,(int *)local_a798,param_2,(int)local_a828,
                             (int)local_a718,&local_a84c,iVar11,0,(int)local_a698,iVar14);
        iVar8 = local_a84c;
        if (iVar9 == -0x8000) {
          return -0x8000;
        }
      }
    }
    local_a854 = local_a854 + 1;
    iVar7 = iVar11;
  } while (local_a854 < 4);
  if (0 < iVar11) {
    puVar19 = local_a500;
    for (iVar14 = iVar11; iVar14 != 0; iVar14 = iVar14 + -1) {
      *puVar19 = 0;
      puVar19 = puVar19 + 1;
    }
  }
  if (local_a85c < iVar8) {
    if (local_a844 == (int *)0x0) {
      iVar14 = 0;
      if (0 < iVar11) {
        do {
          local_a300[iVar14] = local_a618[iVar14] - iVar14 / 2;
          iVar14 = iVar14 + 1;
        } while (iVar14 < iVar11);
      }
    }
    else {
      iVar14 = 0;
      if (0 < iVar11) {
        do {
          local_a300[iVar14] = (local_a618[iVar14] + 1) * 0x20 - iVar14;
          iVar14 = iVar14 + 1;
        } while (iVar14 < iVar11);
      }
    }
    FUN_0043f590((int)local_a300,aiStack_a404 + 1,iVar11);
    iVar14 = iVar11;
    iVar8 = local_a84c;
    if (local_a85c < local_a84c) {
      while (piVar13 = local_a828, iVar8 = local_a84c, 0 < iVar14) {
        iVar7 = aiStack_a404[iVar14];
        iVar14 = iVar14 + -1;
        fVar1 = local_a798[iVar7];
        while (local_a84c = iVar8, 0 < (int)fVar1) {
          if (iVar8 <= local_a85c) goto LAB_0043dd41;
          local_a798[iVar7] = (float)((int)fVar1 + -1);
          local_a500[iVar7] = 1;
          iVar8 = FUN_0043e8c0((int)local_a500,(int *)local_a798,param_2,(int)piVar13,
                               (int)local_a718,&local_a84c,iVar11,0,(int)local_a698,local_a830);
          if (iVar8 == -0x8000) {
            return -0x8000;
          }
          fVar1 = local_a798[iVar7];
          local_a500[iVar7] = 0;
          iVar8 = local_a84c;
        }
        if (iVar8 <= local_a85c) break;
      }
    }
  }
LAB_0043dd41:
  if (iVar11 == 0) {
    local_a798[0] = 0.0;
    *param_3 = 1;
    param_3[1] = 1;
    param_3[4] = 0;
    param_3[0x44] = 0;
    iVar11 = FUN_0043ce00(param_3);
    return iVar11;
  }
  iVar14 = (&iStack_a79c)[iVar11];
  piVar13 = &iStack_a79c + iVar11;
  for (iVar7 = iVar11; (iVar14 == 0 && (1 < iVar7)); iVar7 = iVar7 + -1) {
    iVar14 = piVar13[-1];
    piVar13 = piVar13 + -1;
  }
  iVar14 = 0;
  if (0 < iVar7) {
    piVar13 = param_3 + 0x143f;
    do {
      pfVar16 = local_a798 + iVar14;
      iVar14 = iVar14 + 1;
      piVar13[-0x20] = (int)*pfVar16;
      *piVar13 = aiStack_a284[iVar14];
      piVar13 = piVar13 + 1;
    } while (iVar14 < iVar7);
  }
  param_3[1] = local_a838;
  iVar14 = 0;
  local_a85c = local_a83c - (local_a85c + ((iVar11 - iVar7) * 3 - iVar8));
  *param_3 = iVar7;
  param_3[2] = 1;
  param_3[3] = 0;
  if (0 < iVar7) {
    piVar13 = aiStack_a404;
    for (iVar11 = iVar7; piVar13 = (int *)((int)piVar13 + 4), iVar11 != 0; iVar11 = iVar11 + -1) {
      *piVar13 = -1;
    }
    do {
      if (local_a798[iVar14] == 0.0) {
        local_a598[iVar14] = -9.99;
      }
      else {
        local_a598[iVar14] = afStack_a484[iVar14 + 1] - (float)(int)local_a798[iVar14];
      }
      iVar14 = iVar14 + 1;
    } while (iVar14 < iVar7);
  }
  iVar11 = 1;
  local_a828 = (int *)local_a598[0];
  if (1 < iVar7) {
    do {
      if (local_a598[iVar11] < local_a598[0]) {
        local_a598[0] = local_a598[iVar11];
      }
      if ((float)local_a828 < local_a598[iVar11]) {
        local_a828 = (int *)local_a598[iVar11];
      }
      iVar11 = iVar11 + 1;
    } while (iVar11 < iVar7);
  }
  puVar20 = (undefined *)0x0;
  iVar11 = 0;
  do {
    iVar11 = iVar11 + 1;
    local_a848 = (float)local_a828 -
                 (float)iVar11 * ((float)local_a828 - local_a598[0]) * (float)_DAT_00491430;
    uVar15 = iVar7 - 1U;
    if (-1 < (int)(iVar7 - 1U)) {
      do {
        if ((local_a848 <= local_a598[uVar15]) && (aiStack_a404[uVar15 + 1] == -1)) {
          auStack_a100[(int)puVar20] = uVar15;
          aiStack_a404[uVar15 + 1] = (int)puVar20;
          puVar20 = (undefined *)((int)puVar20 + 1);
        }
        uVar15 = uVar15 - 1;
      } while (uVar15 < 0x80000000);
    }
  } while (iVar11 < 10);
  local_a850 = 0.0;
  local_a834 = puVar20;
  if (0 < (int)puVar20) {
    do {
      uVar15 = auStack_a100[(int)local_a850];
      if (((aiStack_a380[uVar15] == 0) &&
          (local_a848 = (float)param_3[uVar15 + 0x141f], (int)local_a848 < 7)) &&
         (0 < (int)local_a848)) {
        local_a82c = local_a698[uVar15];
        pfVar16 = local_a698 + uVar15;
        if ((int)local_a848 < (int)local_a200[uVar15]) {
          param_3[uVar15 + 0x141f] = (int)local_a848 + 1;
LAB_0043df7d:
          local_a844 = (int *)0x1;
          fVar21 = FUN_0043ebd0((int)*pfVar16,param_3[uVar15 + 0x141f]);
          piVar13 = local_a000;
          iVar14 = local_a830;
          iVar11 = FUN_0043cda0(uVar15);
          iVar11 = param_2 + iVar11 * 4;
          iVar7 = FUN_0043d130(uVar15);
          iVar11 = FUN_0043e9b0(param_3[3],param_3[uVar15 + 0x141f],(float)fVar21,iVar7,iVar11,
                                piVar13,iVar14);
          if (iVar11 == -0x8000) {
            return -0x8000;
          }
          iVar14 = (iVar11 - local_a718[uVar15]) + local_a85c;
          iVar7 = local_a718[uVar15];
        }
        else {
          if (0 < (int)local_a82c) {
            *pfVar16 = (float)((int)local_a82c + -1);
            goto LAB_0043df7d;
          }
          iVar11 = local_a718[uVar15];
          local_a844 = (int *)0x0;
          iVar14 = local_a85c;
          iVar7 = iVar11;
        }
        iVar8 = local_a83c;
        if (local_a83c < iVar14) {
          param_3[uVar15 + 0x141f] = (int)local_a848;
          *pfVar16 = local_a82c;
          puVar20 = local_a834;
        }
        else {
          if (local_a844 != (int *)0x0) {
            local_a84c = local_a84c + (iVar11 - iVar7);
            local_a718[uVar15] = iVar11;
            iVar11 = FUN_0043d130(uVar15);
            iVar14 = extraout_ECX_01;
            local_a85c = extraout_ECX_01;
            if (0 < iVar11) {
              do {
                iVar11 = FUN_0043cda0(uVar15);
                param_3[iVar11 + extraout_EDX_01 + 0x145f] = local_a000[extraout_EDX_01];
                iVar11 = FUN_0043d130(uVar15);
                iVar14 = extraout_ECX_02;
                local_a85c = extraout_ECX_02;
              } while (extraout_EDX_02 < iVar11);
            }
          }
          puVar20 = local_a834;
          if (iVar8 + -8 < iVar14) break;
        }
      }
      local_a850 = (float)((int)local_a850 + 1);
    } while ((int)local_a850 < (int)puVar20);
  }
  iVar11 = 0;
  if (0 < *param_3) {
    local_a844 = param_3 + 0x141f;
    do {
      if ((0 < (int)local_a698[iVar11]) && (iVar14 = *local_a844, 0 < iVar14)) {
        iVar7 = FUN_0043cda0(iVar11);
        iVar8 = FUN_0043d130(iVar11);
        fVar21 = FUN_0043ebd0(0,iVar14);
        iVar14 = FUN_0043e9b0(param_3[3],iVar14,(float)fVar21,iVar8,param_2 + iVar7 * 4,local_a000,
                              local_a830);
        if (iVar14 == -0x8000) {
          return -0x8000;
        }
        iVar7 = local_a85c + (iVar14 - local_a718[iVar11]);
        if (iVar7 <= local_a83c) {
          local_a84c = local_a84c + (iVar14 - local_a718[iVar11]);
          local_a718[iVar11] = iVar14;
          local_a698[iVar11] = 0.0;
          iVar14 = FUN_0043d130(iVar11);
          local_a85c = iVar7;
          if (0 < iVar14) {
            do {
              iVar14 = FUN_0043cda0(iVar11);
              *(int *)(extraout_EDX_03 + 0x517c + (iVar14 + extraout_ECX_03) * 4) =
                   local_a000[extraout_ECX_03];
              iVar14 = FUN_0043d130(iVar11);
            } while (extraout_ECX_04 < iVar14);
          }
        }
      }
      iVar11 = iVar11 + 1;
      local_a844 = local_a844 + 1;
    } while (iVar11 < *param_3);
  }
  local_a854 = 0;
  do {
    if (local_a83c + -2 < local_a85c) break;
    iVar11 = 0;
    if (0 < *param_3) {
      piVar13 = param_3 + 0x141f;
      do {
        if (local_a83c + -2 < local_a85c) break;
        iVar14 = *piVar13;
        if (((iVar14 < (int)local_a200[iVar11]) && (0 < iVar14)) && (aiStack_a380[iVar11] == 0)) {
          *piVar13 = iVar14 + 1;
          fVar21 = FUN_0043ebd0((int)local_a698[iVar11],iVar14 + 1);
          piVar17 = local_a000;
          iVar8 = local_a830;
          iVar7 = FUN_0043cda0(iVar11);
          iVar7 = param_2 + iVar7 * 4;
          iVar9 = FUN_0043d130(iVar11);
          iVar7 = FUN_0043e9b0(param_3[3],*piVar13,(float)fVar21,iVar9,iVar7,piVar17,iVar8);
          if (iVar7 == -0x8000) {
            return -0x8000;
          }
          local_a838 = local_a85c + (iVar7 - local_a718[iVar11]);
          if (local_a83c < local_a838) {
            *piVar13 = iVar14;
            aiStack_a380[iVar11] = 1;
          }
          else {
            local_a84c = local_a84c + (iVar7 - local_a718[iVar11]);
            local_a718[iVar11] = iVar7;
            iVar14 = FUN_0043d130(iVar11);
            if (0 < iVar14) {
              do {
                iVar14 = FUN_0043cda0(iVar11);
                param_3[iVar14 + extraout_ECX_05 + 0x145f] = local_a000[extraout_ECX_05];
                iVar14 = FUN_0043d130(iVar11);
              } while (extraout_ECX_06 < iVar14);
            }
            local_a85c = local_a838;
          }
        }
        iVar11 = iVar11 + 1;
        piVar13 = piVar13 + 1;
      } while (iVar11 < *param_3);
    }
    local_a854 = local_a854 + 1;
  } while (local_a854 < 7);
  iVar11 = *param_3;
  if (1 < iVar11) {
    iVar14 = 0;
    if (0 < iVar11) {
      do {
        aiStack_a404[iVar14 + 1] = (local_a080[iVar14] + 1) * 0x20 - iVar14;
        iVar14 = iVar14 + 1;
      } while (iVar14 < iVar11);
    }
    FUN_0043f590((int)(aiStack_a404 + 1),local_a300,iVar11);
    local_a854 = 0;
    iVar11 = local_a85c;
    do {
      if (local_a83c + -2 < iVar11) break;
      local_a850 = 0.0;
      iVar11 = local_a85c;
      if (0 < *param_3) {
        do {
          if (local_a83c + -2 < iVar11) break;
          iVar14 = local_a300[(int)local_a850];
          iVar7 = param_3[iVar14 + 0x141f];
          if ((iVar7 < local_a854 + 3) && (0 < iVar7)) {
            param_3[iVar14 + 0x141f] = iVar7 + 1;
            fVar21 = FUN_0043ebd0((int)local_a698[iVar14],iVar7 + 1);
            piVar13 = local_a000;
            iVar9 = local_a830;
            iVar8 = FUN_0043cda0(iVar14);
            iVar8 = param_2 + iVar8 * 4;
            iVar10 = FUN_0043d130(iVar14);
            iVar8 = FUN_0043e9b0(param_3[3],param_3[iVar14 + 0x141f],(float)fVar21,iVar10,iVar8,
                                 piVar13,iVar9);
            if (iVar8 == -0x8000) {
              return -0x8000;
            }
            if (local_a83c < iVar11 + (iVar8 - local_a718[iVar14])) {
              param_3[iVar14 + 0x141f] = iVar7;
              iVar11 = local_a85c;
            }
            else {
              local_a84c = local_a84c + (iVar8 - local_a718[iVar14]);
              local_a718[iVar14] = iVar8;
              iVar7 = FUN_0043d130(iVar14);
              iVar11 = extraout_EDX_04;
              local_a85c = extraout_EDX_04;
              if (0 < iVar7) {
                do {
                  iVar11 = FUN_0043cda0(iVar14);
                  param_3[iVar11 + extraout_ECX_07 + 0x145f] = local_a000[extraout_ECX_07];
                  iVar7 = FUN_0043d130(iVar14);
                  iVar11 = extraout_EDX_05;
                  local_a85c = extraout_EDX_05;
                } while (extraout_ECX_08 < iVar7);
              }
            }
          }
          local_a850 = (float)((int)local_a850 + 1);
        } while ((int)local_a850 < *param_3);
      }
      local_a854 = local_a854 + 1;
    } while (local_a854 < 4);
  }
  local_a854 = 0;
  do {
    if (local_a83c + -2 < local_a85c) break;
    iVar11 = 0;
    if (0 < *param_3) {
      piVar13 = param_3 + 0x141f;
      do {
        if (local_a83c + -2 < local_a85c) break;
        iVar14 = *piVar13;
        if ((iVar14 < 7) && (0 < iVar14)) {
          *piVar13 = iVar14 + 1;
          fVar21 = FUN_0043ebd0((int)local_a698[iVar11],iVar14 + 1);
          piVar17 = local_a000;
          iVar8 = local_a830;
          iVar7 = FUN_0043cda0(iVar11);
          iVar7 = param_2 + iVar7 * 4;
          iVar9 = FUN_0043d130(iVar11);
          iVar7 = FUN_0043e9b0(param_3[3],*piVar13,(float)fVar21,iVar9,iVar7,piVar17,iVar8);
          if (iVar7 == -0x8000) {
            return -0x8000;
          }
          local_a838 = local_a85c + (iVar7 - local_a718[iVar11]);
          if (local_a83c < local_a838) {
            *piVar13 = iVar14;
          }
          else {
            local_a84c = local_a84c + (iVar7 - local_a718[iVar11]);
            local_a718[iVar11] = iVar7;
            iVar14 = FUN_0043d130(iVar11);
            if (0 < iVar14) {
              do {
                iVar14 = FUN_0043cda0(iVar11);
                param_3[iVar14 + extraout_ECX_09 + 0x145f] = local_a000[extraout_ECX_09];
                iVar14 = FUN_0043d130(iVar11);
              } while (extraout_ECX_10 < iVar14);
            }
            local_a85c = local_a838;
          }
        }
        iVar11 = iVar11 + 1;
        piVar13 = piVar13 + 1;
      } while (iVar11 < *param_3);
    }
    local_a854 = local_a854 + 1;
  } while (local_a854 < 7);
  iVar11 = 0;
  if (0 < *param_3) {
    piVar13 = param_3 + 0x143f;
    do {
      local_a844 = (int *)0x0;
      local_a848 = 0.0;
      local_a834 = (undefined *)FUN_0043e740(piVar13[-0x20]);
      if (local_a834 == (undefined *)0xffffffff) {
        return -0x8000;
      }
      local_a82c = DAT_0048b434 / ((float)(int)local_a834 + (float)_DAT_00451670);
      FUN_0043cda0(iVar11);
      iVar11 = iVar11 + 1;
      iVar14 = FUN_0043cda0(iVar11);
      fVar22 = (float10)local_a848;
      fVar21 = (float10)(float)local_a844;
      if (extraout_ECX_11 < iVar14) {
        do {
          iVar14 = FUN_0043cda0(iVar11);
          fVar21 = extraout_ST0_00;
          fVar22 = extraout_ST1;
        } while (extraout_ECX_12 < iVar14);
      }
      if ((fVar22 * (float10)_DAT_00491080 < fVar21) && (0 < *piVar13)) {
        *piVar13 = *piVar13 + -1;
      }
      piVar13 = piVar13 + 1;
    } while (iVar11 < *param_3);
  }
  iVar14 = FUN_0043ce00(param_3);
  iVar11 = -0x8000;
  if (local_a85c == iVar14) {
    iVar11 = local_a85c;
  }
  return iVar11;
}


// ============================
// RVA 0x3e740 -> FUN_0043e740

undefined4 __cdecl FUN_0043e740(int param_1)

{
  if ((-1 < param_1) && (param_1 < 8)) {
    return *(undefined4 *)(&DAT_0048ea24 + param_1 * 4);
  }
  return 0xffffffff;
}


// ============================
// RVA 0x3ec60 -> FUN_0043ec60

void __cdecl
FUN_0043ec60(undefined4 param_1,undefined4 *param_2,undefined4 *param_3,undefined4 *param_4)

{
  int iVar1;
  
  for (iVar1 = 6; iVar1 != 0; iVar1 = iVar1 + -1) {
    *param_3 = 0;
    param_3 = param_3 + 1;
  }
  *param_2 = 10;
  *param_4 = 7;
  return;
}


// ============================
// RVA 0x3ec90 -> FUN_0043ec90

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int __cdecl
FUN_0043ec90(int param_1,int param_2,int param_3,float param_4,int param_5,int param_6,int param_7,
            int param_8,int param_9)

{
  float fVar1;
  bool bVar2;
  int iVar3;
  int iVar4;
  int *piVar5;
  int iVar6;
  int *piVar7;
  int *piVar8;
  int *piVar9;
  float10 fVar10;
  int in_stack_ffffff50;
  int in_stack_ffffff54;
  int local_60;
  int local_58;
  int local_4c;
  int local_48;
  int local_40 [16];
  
  local_60 = 0;
  bVar2 = false;
  local_48 = 0;
  do {
    if (!bVar2) {
      iVar4 = 0;
      iVar6 = 0;
      piVar8 = local_40;
      for (iVar3 = 0x10; iVar3 != 0; iVar3 = iVar3 + -1) {
        *piVar8 = 0;
        piVar8 = piVar8 + 1;
      }
      if (0 < param_2) {
        fVar1 = param_4 + _DAT_00491138;
        piVar8 = (int *)(param_6 + 4);
        do {
          iVar3 = (int)(iVar6 + (iVar6 >> 0x1f & 0xfU)) >> 4;
          if (fVar1 < (float)*piVar8) {
            if ((local_40[iVar3] < 7) && (*(int *)(param_8 + 0x4278) + iVar4 < 0x40)) {
              iVar4 = iVar4 + 1;
              local_40[iVar3] = local_40[iVar3] + 1;
            }
          }
          iVar6 = iVar6 + 1;
          piVar8 = piVar8 + 0x12;
        } while (iVar6 < param_2);
        if (0 < iVar4) {
          iVar3 = param_3 + 6 + local_60;
          if (param_1 < iVar3) {
            bVar2 = true;
          }
          else {
            iVar4 = *(int *)(param_8 + 0x110);
            *(int *)(param_8 + 0x110) = iVar4 + 1;
            piVar8 = (int *)(param_8 + 0x114 + iVar4 * 0x21c);
            *piVar8 = 7;
            piVar8[1] = 3;
            piVar8[2] = 1;
            piVar8[3] = 0;
            piVar8[4] = 0;
            piVar8[5] = 0;
            piVar8[6] = 0;
            piVar5 = piVar8 + 7;
            for (iVar4 = 0x10; iVar4 != 0; iVar4 = iVar4 + -1) {
              *piVar5 = 0;
              piVar5 = piVar5 + 1;
            }
            local_58 = param_7;
            iVar4 = param_6 - param_5;
            local_4c = 0;
            piVar5 = (int *)(param_5 + 4);
            local_60 = iVar3;
            do {
              iVar3 = local_4c + (local_4c >> 0x1f & 0xfU);
              iVar6 = iVar3 >> 4;
              iVar3 = (int)((iVar3 >> 0x1f & 3U) + iVar6) >> 2;
              if (((fVar1 < (float)*(int *)(iVar4 + (int)piVar5)) && (piVar8[iVar6 + 7] < 7)) &&
                 (*(int *)(param_8 + 0x4278) < 0x40)) {
                if (piVar8[iVar3 + 3] == 0) {
                  if (param_1 < local_60 + 0xc) {
                    bVar2 = true;
                  }
                  else {
                    piVar8[iVar3 + 3] = 1;
                    local_60 = local_60 + 0xc;
                  }
                }
                if (piVar8[iVar3 + 3] == 1) {
                  if (param_1 < local_60 + 0xc +
                                *(int *)(&UNK_0048ebe8 + (*piVar8 + piVar8[2] * 8) * 4) * 4) {
                    bVar2 = true;
                  }
                  else {
                    piVar7 = (int *)(param_8 + 0x427c + *(int *)(param_8 + 0x4278) * 0x38);
                    *(int *)(param_8 + 0x4278) = *(int *)(param_8 + 0x4278) + 1;
                    piVar8[iVar6 * 7 + piVar8[iVar6 + 7] + 0x17] = (int)piVar7;
                    piVar8[iVar6 + 7] = piVar8[iVar6 + 7] + 1;
                    *piVar7 = local_4c * 4;
                    piVar7[1] = *piVar5;
                    piVar7[0xb] = *piVar8;
                    piVar7[10] = piVar8[1];
                    piVar7[0xc] = piVar8[2];
                    iVar3 = FUN_0043efc0(param_7,piVar7,param_9);
                    if (iVar3 == -0x8000) {
                      return -0x8000;
                    }
                    local_60 = local_60 + iVar3;
                    piVar9 = (int *)&stack0xffffff50;
                    for (iVar3 = 0xe; iVar3 != 0; iVar3 = iVar3 + -1) {
                      *piVar9 = *piVar7;
                      piVar7 = piVar7 + 1;
                      piVar9 = piVar9 + 1;
                    }
                    iVar3 = FUN_0043f6e0(in_stack_ffffff50,in_stack_ffffff54);
                    if (iVar3 == -1) {
                      return -0x8000;
                    }
                    fVar10 = (float10)FUN_0043fd90(local_58,4);
                    iVar3 = FUN_0043eb70((float)fVar10);
                    *(int *)(iVar4 + (int)piVar5) =
                         *(int *)(iVar4 + (int)piVar5) + (iVar3 - *piVar5);
                    *piVar5 = iVar3;
                  }
                }
              }
              local_4c = local_4c + 1;
              local_58 = local_58 + 0x10;
              piVar5 = piVar5 + 0x12;
            } while (local_4c < param_2);
          }
        }
      }
    }
    local_48 = local_48 + 1;
    if (1 < local_48) {
      return local_60;
    }
  } while( true );
}


// ============================
// RVA 0x3f110 -> FUN_0043f110

undefined4 __cdecl FUN_0043f110(int param_1)

{
  int iVar1;
  int iVar2;
  undefined4 uVar3;
  uint uVar4;
  int *piVar5;
  int iVar6;
  int *piVar7;
  int local_1c;
  int local_18 [4];
  uint local_8 [2];
  
  iVar1 = 0;
  piVar7 = (int *)(param_1 + 4);
  uVar4 = 0;
  local_18[2] = 0;
  iVar6 = 0;
  piVar5 = piVar7;
  do {
    if (*(int *)(iVar6 + 4 + param_1) < *piVar5) {
      iVar6 = iVar1;
      local_18[2] = uVar4;
    }
    iVar1 = iVar1 + 0x48;
    uVar4 = uVar4 + 1;
    piVar5 = piVar5 + 0x12;
  } while (iVar1 < 0x4800);
  local_8[0] = local_18[2] & 0x8000003f;
  if ((int)local_8[0] < 0) {
    local_8[0] = (local_8[0] - 1 | 0xffffffc0) + 1;
  }
  local_18[0] = (int)(local_18[2] + (local_18[2] >> 0x1f & 0x3fU)) >> 6;
  if ((int)local_8[0] < 0x20) {
    local_18[1] = local_18[0] + -1;
  }
  else {
    local_18[1] = local_18[0] + 1;
  }
  iVar6 = 0;
  local_8[1] = 0x3f - local_8[0];
  local_1c = 0;
  iVar1 = 0;
LAB_0043f18c:
  iVar2 = 0;
LAB_0043f18e:
  if (local_1c != local_18[iVar2]) goto code_r0x0043f194;
  if (-1 < iVar2) {
    uVar4 = local_8[iVar2];
    iVar2 = uVar4 - 2;
    piVar5 = piVar7;
    if (0 < iVar2) {
      do {
        if (iVar6 < *piVar5) {
          iVar6 = *piVar5;
        }
        iVar2 = iVar2 + -1;
        piVar5 = piVar5 + 0x12;
      } while (iVar2 != 0);
    }
    if (((int)(uVar4 + 2) < 0x3f) && (iVar2 = uVar4 + 3, iVar2 < 0x40)) {
      piVar5 = (int *)(param_1 + 4 + (iVar2 + iVar1) * 0x48);
      iVar2 = 0x40 - iVar2;
      do {
        if (iVar6 < *piVar5) {
          iVar6 = *piVar5;
        }
        piVar5 = piVar5 + 0x12;
        iVar2 = iVar2 + -1;
      } while (iVar2 != 0);
    }
    goto LAB_0043f20b;
  }
  goto LAB_0043f1a0;
code_r0x0043f194:
  iVar2 = iVar2 + 1;
  if (1 < iVar2) goto LAB_0043f1a0;
  goto LAB_0043f18e;
LAB_0043f1a0:
  iVar2 = 0x40;
  piVar5 = piVar7;
  do {
    if (iVar6 < *piVar5) {
      iVar6 = *piVar5;
    }
    piVar5 = piVar5 + 0x12;
    iVar2 = iVar2 + -1;
  } while (iVar2 != 0);
LAB_0043f20b:
  iVar1 = iVar1 + 0x40;
  local_1c = local_1c + 1;
  piVar7 = piVar7 + 0x480;
  if (0xff < iVar1) {
    uVar3 = 0;
    iVar2 = *(int *)(param_1 + 4 + local_18[2] * 0x48);
    iVar1 = iVar2 + -0x11;
    if (iVar1 < 10) {
      iVar1 = 9;
    }
    if (iVar6 < iVar1) {
      if (0x23 < iVar2) {
        return 2;
      }
      if (0x14 < iVar2) {
        uVar3 = 1;
      }
    }
    return uVar3;
  }
  goto LAB_0043f18c;
}


// ============================
// RVA 0x3f7d0 -> FUN_0043f7d0

int __cdecl FUN_0043f7d0(int *param_1,int param_2,int param_3)

{
  int iVar1;
  int iVar2;
  
  iVar1 = param_1[0x187d];
  param_1[0x1873] = (int)(param_2 + 7 + (param_2 + 7 >> 0x1f & 7U)) >> 3;
  if ((param_1[0x1860] != 1) || (*(int *)(iVar1 + 0x10) != 0)) {
    iVar2 = FUN_0043f840(param_1,(int *)(*(int *)(iVar1 + 0x18) + param_3),param_2);
    if ((iVar2 != -1) && ((*(int *)(iVar1 + 0x10) != 1 && (*(int *)(iVar1 + 0xc) != 2)))) {
      *(int *)(iVar1 + 0x18) = *(int *)(iVar1 + 0x18) + param_1[0x1871];
      return iVar2;
    }
  }
  return -1;
}


// ============================
// RVA 0x3f840 -> FUN_0043f840

int __cdecl FUN_0043f840(int *param_1,int *param_2,int param_3)

{
  uint *puVar1;
  int *piVar2;
  int *piVar3;
  int *piVar4;
  int iVar5;
  uint uVar6;
  int iVar7;
  int iVar8;
  int iVar9;
  int extraout_ECX;
  int iVar10;
  int *piVar11;
  uint local_1c;
  int *local_18;
  int *local_14;
  int *local_10;
  int local_c;
  int local_8;
  int local_4;
  
  piVar4 = param_2;
  piVar3 = param_1;
  local_1c = 0;
  if (param_1[0x1860] != 1) {
    FUN_00440190(0x28,6,(int)param_2,&local_1c);
    FUN_00440190(param_1[1] + -1,2,(int)param_2,&local_1c);
    param_2 = (int *)0x0;
    if (0 < param_1[1]) {
      piVar11 = param_1 + 4;
      do {
        FUN_00440190(*piVar11,3,(int)piVar4,&local_1c);
        param_1 = (int *)0x0;
        piVar2 = piVar11;
        if (0 < *piVar11) {
          do {
            FUN_00440190(piVar2[8],4,(int)piVar4,&local_1c);
            FUN_00440190(piVar2[1],5,(int)piVar4,&local_1c);
            param_1 = (int *)((int)param_1 + 1);
            piVar2 = piVar2 + 1;
          } while ((int)param_1 < *piVar11);
        }
        param_2 = (int *)((int)param_2 + 1);
        piVar11 = piVar11 + 0x10;
      } while ((int)param_2 < piVar3[1]);
    }
    FUN_00440190(piVar3[0x44],5,(int)piVar4,&local_1c);
    if (0 < piVar3[0x44]) {
      FUN_00440190(piVar3[2],2,(int)piVar4,&local_1c);
    }
    piVar3[0x109e] = 0;
    local_8 = 0;
    if (0 < piVar3[0x44]) {
      local_18 = piVar3 + 0x45;
      do {
        iVar10 = 0;
        if (0 < piVar3[1]) {
          piVar11 = local_18 + 3;
          do {
            FUN_00440190(*piVar11,1,(int)piVar4,&local_1c);
            iVar10 = iVar10 + 1;
            piVar11 = piVar11 + 1;
          } while (iVar10 < piVar3[1]);
        }
        FUN_00440190(local_18[1],3,(int)piVar4,&local_1c);
        piVar11 = local_18;
        FUN_00440190(*local_18,3,(int)piVar4,&local_1c);
        if (piVar3[2] == 3) {
          return -1;
        }
        iVar10 = *piVar11;
        iVar5 = FUN_0043fcb0(iVar10);
        if (iVar5 == -1) {
          return -1;
        }
        iVar5 = FUN_0043d060(piVar11[1]);
        if (iVar5 == -1) {
          return -1;
        }
        local_4 = iVar10 * 0x30 + *(int *)(*(int *)(piVar3[0x187d] + 0x28) + piVar11[2] * 4);
        local_c = 0;
        if (0 < piVar3[1] << 2) {
          local_10 = piVar11 + 0x17;
          param_2 = piVar11 + 7;
          do {
            iVar10 = FUN_0043d040(local_c);
            if (iVar10 == -1) {
              return -1;
            }
            if (piVar11[iVar10 + 3] != 0) {
              FUN_00440190(*param_2,3,(int)piVar4,&local_1c);
              param_1 = (int *)0x0;
              if (0 < *param_2) {
                local_14 = local_10;
                do {
                  piVar3[0x109e] = piVar3[0x109e] + 1;
                  puVar1 = (uint *)*local_14;
                  FUN_00440190(puVar1[1],6,(int)piVar4,&local_1c);
                  uVar6 = *puVar1 & 0x8000003f;
                  if ((int)uVar6 < 0) {
                    uVar6 = (uVar6 - 1 | 0xffffffc0) + 1;
                  }
                  FUN_00440190(uVar6,6,(int)piVar4,&local_1c);
                  if (0x400 < (int)(*puVar1 + iVar5)) {
                    iVar5 = 0x400 - *puVar1;
                  }
                  iVar10 = FUN_0043fcd0(local_4,(int)(puVar1 + 2),iVar5,(int)piVar4,&local_1c);
                  if (iVar10 == -1) {
                    return -1;
                  }
                  param_1 = (int *)((int)param_1 + 1);
                  local_14 = local_14 + 1;
                  piVar11 = local_18;
                } while ((int)param_1 < *param_2);
              }
            }
            local_10 = local_10 + 7;
            local_c = local_c + 1;
            param_2 = param_2 + 1;
          } while (local_c < piVar3[1] * 4);
        }
        local_8 = local_8 + 1;
        local_18 = piVar11 + 0x87;
      } while (local_8 < piVar3[0x44]);
    }
    FUN_00440190(*piVar3 + -1,5,(int)piVar4,&local_1c);
    FUN_00440190(piVar3[3],1,(int)piVar4,&local_1c);
    iVar10 = 0;
    if (0 < *piVar3) {
      do {
        FUN_00440190(piVar3[iVar10 + 0x141f],3,(int)piVar4,&local_1c);
        iVar10 = iVar10 + 1;
      } while (iVar10 < *piVar3);
    }
    param_1 = (int *)0x0;
    if (0 < *piVar3) {
      piVar11 = piVar3 + 0x143f;
      iVar10 = 0x507c - (int)piVar11;
      do {
        if (0 < *(int *)((int)piVar11 + (int)piVar3 + iVar10)) {
          FUN_00440190(*piVar11,6,(int)piVar4,&local_1c);
        }
        param_1 = (int *)((int)param_1 + 1);
        piVar11 = piVar11 + 1;
      } while ((int)param_1 < *piVar3);
    }
    iVar10 = piVar3[3];
    iVar5 = 0;
    if (0 < *piVar3) {
      do {
        iVar9 = piVar3[iVar5 + 0x141f];
        iVar7 = FUN_0043fcb0(iVar9);
        if (iVar7 == -1) {
          return -1;
        }
        if (0 < iVar7) {
          iVar7 = *(int *)(*(int *)(piVar3[0x187d] + 0x24) + iVar10 * 4);
          iVar8 = FUN_0043cda0(iVar5);
          if (iVar8 == -1) {
            return -1;
          }
          iVar8 = FUN_0043d130(iVar5);
          if (iVar8 == -1) {
            return -1;
          }
          iVar9 = FUN_0043fcd0(iVar9 * 0x30 + iVar7,(int)(piVar3 + extraout_ECX + 0x145f),iVar8,
                               (int)piVar4,&local_1c);
          if (iVar9 == -1) {
            return -1;
          }
        }
        iVar5 = iVar5 + 1;
      } while (iVar5 < *piVar3);
    }
    if ((int)local_1c <= param_3) {
      return local_1c;
    }
  }
  return -1;
}


// ============================
// RVA 0x3fcb0 -> FUN_0043fcb0

undefined4 __cdecl FUN_0043fcb0(int param_1)

{
  if ((-1 < param_1) && (param_1 < 8)) {
    return *(undefined4 *)(&DAT_0048ea04 + param_1 * 4);
  }
  return 0xffffffff;
}


// ============================
// RVA 0x40b30 -> FUN_00440b30

/* WARNING: Function: __alloca_probe replaced with injection: alloca_probe */

void __cdecl FUN_00440b30(float *param_1,int *param_2,int param_3)

{
  float local_1000 [512];
  float local_800 [511];
  undefined4 uStack_4;
  
  uStack_4 = 0x440b3a;
  FUN_00440bc0(param_1,(int)local_1000,local_800,0x400,(float *)(param_3 + 0x5000));
  FUN_00440bc0(local_1000,*param_2,(float *)param_2[1],0x200,(float *)(param_3 + 0x50b8));
  FUN_00440bc0(local_800,param_2[3],(float *)param_2[2],0x200,(float *)(param_3 + 0x5170));
  return;
}


// ============================
// RVA 0x40cb0 -> FUN_00440cb0

int __cdecl FUN_00440cb0(int *param_1,float *param_2,int *param_3)

{
  int iVar1;
  float *pfVar2;
  int iVar3;
  
  iVar3 = 0;
  pfVar2 = param_2;
  do {
    iVar1 = FUN_00440d20(param_1[iVar3],0x200,pfVar2,
                         (int *)(((int)param_3 - (int)param_2) + (int)pfVar2));
    if (iVar1 == -1) {
      return -1;
    }
    iVar3 = iVar3 + 1;
    pfVar2 = pfVar2 + 0x10;
  } while (iVar3 < 4);
  iVar3 = FUN_004414f0(param_1,4,0x200,(int *)param_2,param_3);
  return (iVar3 != -1) - 1;
}


// ============================
// RVA 0x414f0 -> FUN_004414f0

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 __cdecl FUN_004414f0(int *param_1,int param_2,int param_3,int *param_4,int *param_5)

{
  bool bVar1;
  int iVar2;
  int iVar3;
  int *piVar4;
  float *pfVar5;
  int iVar6;
  int *piVar7;
  int iVar8;
  int local_14;
  int aiStack_10 [4];
  
  if (1 < param_2) {
    local_14 = 0;
    piVar7 = param_5;
    if (0 < param_2) {
      do {
        iVar3 = *piVar7;
        iVar8 = 0;
        if (iVar3 < 1) {
          aiStack_10[local_14] = 0;
        }
        else {
          iVar2 = 0;
          iVar6 = 4;
          if (0 < iVar3) {
            piVar4 = piVar7 + 8;
            do {
              if (*piVar4 < iVar6) {
                iVar6 = *piVar4;
                iVar8 = iVar2;
              }
              iVar2 = iVar2 + 1;
              piVar4 = piVar4 + 1;
            } while (iVar2 < iVar3);
          }
          iVar3 = 0;
          if (-1 < iVar8) {
            piVar4 = piVar7 + 8;
            iVar8 = iVar8 + 1;
            do {
              if (iVar3 < *piVar4) {
                iVar3 = *piVar4;
              }
              piVar4 = piVar4 + 1;
              iVar8 = iVar8 + -1;
            } while (iVar8 != 0);
          }
          aiStack_10[local_14] = iVar3 - iVar6;
        }
        local_14 = local_14 + 1;
        piVar7 = piVar7 + 0x10;
      } while (local_14 < param_2);
    }
    if (((1 < aiStack_10[1]) && (*param_4 == 0)) && (*param_5 == 0)) {
      iVar3 = param_5[0x11];
      bVar1 = (float)param_4[0xf] <= _DAT_00491160;
      iVar8 = (iVar3 + 1) * ((int)(param_3 + (param_3 >> 0x1f & 0x3fU)) >> 6);
      if (0 < iVar8) {
        pfVar5 = (float *)(*param_1 + (param_3 / 2) * 4);
        do {
          if ((float)_DAT_00491158 < ABS(*pfVar5)) {
            bVar1 = false;
          }
          pfVar5 = pfVar5 + 1;
          iVar8 = iVar8 + -1;
        } while (iVar8 != 0);
      }
      if (bVar1) {
        *param_5 = 1;
        iVar8 = FUN_004414b0(1);
        param_5[8] = iVar8;
        if (iVar8 == -1) {
          return 0xffffffff;
        }
        param_5[1] = iVar3;
      }
    }
  }
  return 0;
}


// ============================
// RVA 0x3c5d0 -> FUN_0043c5d0

/* WARNING: Function: __alloca_probe replaced with injection: alloca_probe */

uint __cdecl
FUN_0043c5d0(short *param_1,undefined4 *param_2,undefined4 *param_3,int param_4,int param_5,
            undefined4 param_6)

{
  int iVar1;
  int iVar2;
  undefined1 *puVar3;
  uint uVar4;
  uint uVar5;
  undefined4 *puVar6;
  int local_2008 [2];
  undefined1 local_2000 [8188];
  undefined4 uStack_4;
  
  uStack_4 = 0x43c5da;
  if ((param_3[2] == 2) && (param_4 < 0x801)) {
    iVar1 = 0;
    if (0 < param_5) {
      puVar3 = local_2000;
      do {
        local_2008[iVar1] = (int)puVar3;
        iVar1 = iVar1 + 1;
        puVar3 = puVar3 + 0x1000;
      } while (iVar1 < param_5);
    }
    iVar1 = 2;
    do {
      param_3[iVar1 + 0x15] = param_3[iVar1 + 0x14];
      iVar1 = iVar1 + -1;
    } while (0 < iVar1);
    iVar1 = FUN_0043d150(param_4,(int)local_2008,param_1,0x400,2,param_5);
    param_3[0x15] = iVar1;
    iVar1 = param_3[0x17];
    uVar5 = param_3[0x10];
    puVar6 = param_2;
    for (uVar4 = uVar5 >> 2; uVar4 != 0; uVar4 = uVar4 - 1) {
      *puVar6 = 0;
      puVar6 = puVar6 + 1;
    }
    for (uVar5 = uVar5 & 3; uVar5 != 0; uVar5 = uVar5 - 1) {
      *(undefined1 *)puVar6 = 0;
      puVar6 = (undefined4 *)((int)puVar6 + 1);
    }
    iVar2 = FUN_0043c9e0((int)local_2008,param_2,param_3,2,param_6);
    if (iVar2 != -1) {
      return (uint)(iVar1 < 0x376);
    }
  }
  return 0xffffffff;
}


// ============================
// RVA 0x3c9e0 -> FUN_0043c9e0

/* WARNING: Function: __alloca_probe replaced with injection: alloca_probe */
/* WARNING: Type propagation algorithm not settling */

undefined4 __cdecl
FUN_0043c9e0(int param_1,undefined4 *param_2,undefined4 *param_3,int param_4,undefined4 param_5)

{
  bool bVar1;
  int *piVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  uint uVar6;
  uint uVar7;
  undefined4 *puVar8;
  int iVar9;
  undefined4 *puVar10;
  undefined4 *local_4120;
  int local_411c [3];
  int local_4110 [4];
  int local_4100 [64];
  undefined4 local_4000 [2048];
  undefined4 local_2000 [2047];
  undefined4 uStack_4;
  
  uStack_4 = 0x43c9ea;
  iVar9 = 0;
  param_3[6] = 0;
  piVar2 = local_4100;
  iVar5 = 4;
  do {
    *piVar2 = 0;
    piVar2 = piVar2 + 0x10;
    iVar5 = iVar5 + -1;
  } while (iVar5 != 0);
  if (0 < param_4) {
    local_4120 = local_4000;
    do {
      local_411c[0] = *(int *)(param_3[0xb] + iVar9 * 4);
      iVar5 = *(int *)(local_411c[0] + 0x61ec);
      FUN_0043cdc0(iVar5);
      *(undefined4 *)(iVar5 + 0x61e8) = *(undefined4 *)(param_3[0xb] + iVar9 * 4);
      *(undefined4 *)(iVar5 + 0x61ec) = *(undefined4 *)(local_411c[0] + 0x61e8);
      iVar4 = 0x61a4;
      do {
        iVar3 = iVar4 + 4;
        *(undefined4 *)(iVar5 + -0x24 + iVar3) = *(undefined4 *)(iVar4 + *(int *)(iVar5 + 0x61e8));
        iVar4 = iVar3;
      } while (iVar3 < 0x61b4);
      iVar9 = iVar9 + 1;
      *(undefined4 *)(iVar5 + 0x61b4) = *(undefined4 *)(*(int *)(iVar5 + 0x61e8) + 0x61bc);
      iVar4 = param_3[0xb];
      local_411c[iVar9] = (int)local_4120;
      local_4120 = local_4120 + 0x400;
      *(int *)(iVar4 + -4 + iVar9 * 4) = iVar5;
    } while (iVar9 < param_4);
  }
  *param_3 = param_5;
  iVar5 = 0;
  if (0 < param_4) {
    do {
      iVar5 = iVar5 + 1;
      *(undefined4 *)(*(int *)(param_3[0xb] + -4 + iVar5 * 4) + 0x61e0) = *param_3;
    } while (iVar5 < param_4);
  }
  iVar5 = 0;
  if (0 < param_4) {
    do {
      iVar9 = *(int *)(param_3[0xb] + iVar5 * 4);
      if (((param_3[2] == 2) && (param_3[3] == 2)) && (*(int *)(iVar9 + 0x61e4) == 1)) {
        return 0xffffffff;
      }
      iVar5 = iVar5 + 1;
      *(undefined4 *)(iVar9 + 0x6180) = 0;
    } while (iVar5 < param_4);
  }
  iVar5 = 0;
  if (0 < param_4) {
    do {
      iVar9 = *(int *)(param_3[0xb] + iVar5 * 4);
      iVar5 = iVar5 + 1;
      *(int *)(iVar9 + 0x61c8) = *(int *)(iVar9 + 0x61c4) << 3;
    } while (iVar5 < param_4);
  }
  iVar5 = 0;
  if (0 < param_4) {
    do {
      iVar5 = iVar5 + 1;
      puVar8 = *(undefined4 **)(param_3[0xb] + -4 + iVar5 * 4);
      *puVar8 = puVar8[0x1876];
      puVar8[1] = puVar8[0x1877];
    } while (iVar5 < param_4);
  }
  iVar5 = FUN_00440960(param_1,(int)(local_411c + 1),(int *)param_3[0xb],(int *)param_3[0xc],param_4
                       ,param_3[3]);
  if (iVar5 == -1) {
    return 0xffffffff;
  }
  iVar5 = 0;
  if (0 < param_4) {
    local_4120 = (undefined4 *)0x0;
    do {
      local_411c[0] = 0;
      iVar9 = *(int *)(param_3[0xb] + iVar5 * 4);
      iVar4 = 0;
      piVar2 = (int *)(iVar9 + 0x10);
      do {
        if ((*piVar2 != 0) || (*(int *)(*(int *)(iVar9 + 0x61e8) + 0x10 + iVar4) != 0)) {
          bVar1 = true;
          goto LAB_0043cbc6;
        }
        iVar4 = iVar4 + 0x40;
        piVar2 = piVar2 + 0x10;
      } while (iVar4 < 0x100);
      bVar1 = false;
LAB_0043cbc6:
      iVar9 = param_3[0xc];
      iVar4 = 0;
      piVar2 = local_411c + 3;
      do {
        iVar3 = iVar4 + 0x400;
        iVar4 = iVar4 + 0xc00;
        *piVar2 = iVar3 + *(int *)(iVar9 + iVar5 * 4);
        piVar2 = piVar2 + 1;
      } while (iVar4 < 0x3000);
      if (bVar1) {
        iVar9 = FUN_004402a0(local_411c + 3,(int)local_2000 + (int)local_4120,local_4100,
                             (int)local_4100,4,(float *)(*(int *)(iVar9 + iVar5 * 4) + 0x4000));
        if (iVar9 == -1) {
          return 0xffffffff;
        }
      }
      else {
        piVar2 = local_411c + 3;
        puVar8 = (undefined4 *)((int)local_4000 + (int)local_4120);
        puVar10 = (undefined4 *)((int)local_2000 + (int)local_4120);
        for (iVar4 = 0x400; iVar4 != 0; iVar4 = iVar4 + -1) {
          *puVar10 = *puVar8;
          puVar8 = puVar8 + 1;
          puVar10 = puVar10 + 1;
        }
        iVar4 = 0x4000;
        do {
          puVar8 = (undefined4 *)*piVar2;
          puVar10 = (undefined4 *)(*(int *)(iVar9 + iVar5 * 4) + iVar4);
          iVar4 = iVar4 + 0x400;
          piVar2 = piVar2 + 1;
          for (iVar3 = 0x100; iVar3 != 0; iVar3 = iVar3 + -1) {
            *puVar10 = *puVar8;
            puVar8 = puVar8 + 1;
            puVar10 = puVar10 + 1;
          }
        } while (iVar4 < 0x5000);
      }
      iVar5 = iVar5 + 1;
      local_4120 = (undefined4 *)((int)local_4120 + 0x1000);
    } while (iVar5 < param_4);
  }
  uVar7 = param_3[5];
  puVar8 = param_2;
  for (uVar6 = uVar7 >> 2; uVar6 != 0; uVar6 = uVar6 - 1) {
    *puVar8 = 0;
    puVar8 = puVar8 + 1;
  }
  for (uVar7 = uVar7 & 3; uVar7 != 0; uVar7 = uVar7 - 1) {
    *(undefined1 *)puVar8 = 0;
    puVar8 = (undefined4 *)((int)puVar8 + 1);
  }
  iVar5 = 0;
  if (0 < param_4) {
    iVar9 = 0;
    do {
      piVar2 = (int *)((int *)param_3[0xb])[iVar5];
      piVar2[0x187c] = *(int *)param_3[0xb];
      if (piVar2[0x1871] < 0x15) {
        piVar2[0x186d] = 0xf;
        piVar2[0x1861] = 3;
        piVar2[0x1862] = 3;
        piVar2[0x1863] = 3;
        piVar2[0x1864] = 3;
        piVar2[1] = 1;
        piVar2[4] = 0;
        piVar2[0x44] = 0;
        *piVar2 = 1;
        piVar2[3] = 0;
        piVar2[0x141f] = 0;
        iVar4 = FUN_0043ce00(piVar2);
      }
      else {
        iVar4 = FUN_0043d1f0((int)local_2000 + iVar9,(int)local_4000 + iVar9,piVar2,piVar2[0x187a]);
      }
      if (iVar4 == -0x8000) {
        return 0xffffffff;
      }
      iVar4 = FUN_0043f7d0(piVar2,iVar4,(int)param_2);
      if (iVar4 == -1) {
        return 0xffffffff;
      }
      iVar5 = iVar5 + 1;
      iVar9 = iVar9 + 0x1000;
    } while (iVar5 < param_4);
  }
  return 0;
}


// ============================
// RVA 0x3d150 -> FUN_0043d150

int __cdecl FUN_0043d150(int param_1,int param_2,short *param_3,int param_4,int param_5,int param_6)

{
  int iVar1;
  int iVar2;
  short *psVar3;
  int iVar4;
  int iVar5;
  undefined4 *puVar6;
  
  if (param_5 == 2) {
    iVar5 = 0;
    iVar1 = param_1 / param_6;
    if (0 < param_6) {
      do {
        iVar4 = *(int *)(param_2 + iVar5 * 4);
        iVar2 = 0;
        psVar3 = param_3;
        if (0 < iVar1) {
          do {
            iVar2 = iVar2 + 1;
            *(float *)(iVar4 + -4 + iVar2 * 4) = (float)(int)*psVar3;
            psVar3 = psVar3 + param_6;
          } while (iVar2 < iVar1);
        }
        iVar5 = iVar5 + 1;
        param_3 = param_3 + 1;
      } while (iVar5 < param_6);
    }
    iVar5 = 0;
    if (0 < param_6) {
      do {
        if (iVar1 < param_4) {
          puVar6 = (undefined4 *)(*(int *)(param_2 + iVar5 * 4) + iVar1 * 4);
          for (iVar4 = param_4 - iVar1; iVar4 != 0; iVar4 = iVar4 + -1) {
            *puVar6 = 0;
            puVar6 = puVar6 + 1;
          }
        }
        iVar5 = iVar5 + 1;
      } while (iVar5 < param_6);
    }
    return iVar1;
  }
  return -1;
}


// ============================
// RVA 0x40470 -> FUN_00440470

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 __cdecl FUN_00440470(int param_1,int param_2)

{
  float fVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  int *piVar7;
  float10 fVar8;
  int in_stack_00000048;
  int in_stack_00000088;
  int local_110;
  int local_10c;
  int local_100 [64];
  
  iVar5 = 0;
  iVar6 = 0;
  piVar7 = local_100;
  for (iVar2 = 0x40; iVar2 != 0; iVar2 = iVar2 + -1) {
    *piVar7 = 0;
    piVar7 = piVar7 + 1;
  }
  if (0 < in_stack_00000048) {
    do {
      iVar2 = FUN_00440600(*(int *)(&stack0x00000068 + iVar5 * 4));
      if (iVar2 == -5) {
        return 0xffffffff;
      }
      if (iVar6 <= *(int *)(&stack0x0000004c + iVar5 * 4) + 0x20) {
        iVar3 = ((*(int *)(&stack0x0000004c + iVar5 * 4) + 0x20) - iVar6) + 1;
        piVar7 = local_100 + iVar6;
        for (iVar4 = iVar3; iVar4 != 0; iVar4 = iVar4 + -1) {
          *piVar7 = iVar2;
          piVar7 = piVar7 + 1;
        }
        iVar6 = iVar6 + iVar3;
      }
      iVar5 = iVar5 + 1;
    } while (iVar5 < in_stack_00000048);
  }
  iVar5 = 0;
  iVar2 = 0;
  if (0 < param_2) {
    do {
      iVar6 = FUN_00440600(*(int *)(&stack0x00000028 + iVar5 * 4));
      if (iVar6 == -5) {
        return 0xffffffff;
      }
      iVar4 = *(int *)(&stack0x0000000c + iVar5 * 4);
      for (; iVar2 <= iVar4; iVar2 = iVar2 + 1) {
        local_100[iVar2] = local_100[iVar2] + iVar6;
      }
      iVar5 = iVar5 + 1;
    } while (iVar5 < param_2);
  }
  local_10c = 0x3f;
  iVar2 = param_1 + -1;
  iVar5 = 0;
  do {
    iVar6 = -local_100[local_10c];
    if (-iVar5 == local_100[local_10c]) {
      if (iVar6 < 0) {
        fVar1 = (float)_DAT_00491458 / (float)(1 << (-(byte)iVar6 & 0x1f));
      }
      else {
        fVar1 = (float)(1 << ((byte)iVar6 & 0x1f));
      }
      iVar5 = 8;
      do {
        iVar2 = iVar2 + -1;
        iVar5 = iVar5 + -1;
        *(float *)(in_stack_00000088 + 4 + iVar2 * 4) = fVar1;
      } while (iVar5 != 0);
    }
    else {
      local_110 = 8;
      do {
        fVar8 = (float10)_CIpow();
        *(float *)(in_stack_00000088 + iVar2 * 4) = (float)fVar8;
        iVar2 = iVar2 + -1;
        local_110 = local_110 + -1;
      } while (local_110 != 0);
    }
    local_10c = local_10c + -1;
    iVar5 = iVar6;
  } while (-1 < local_10c);
  return 0;
}


// ============================
// RVA 0x40960 -> FUN_00440960

undefined4 __cdecl
FUN_00440960(int param_1,int param_2,int *param_3,int *param_4,int param_5,int param_6)

{
  float *pfVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  int iVar7;
  int iVar8;
  undefined4 *puVar9;
  int *local_78;
  int local_70;
  int local_6c;
  int local_60 [8];
  int local_40 [8];
  int local_20 [8];
  
  if (0 < param_5) {
    local_78 = param_4;
    local_6c = param_5;
    iVar8 = 0;
    do {
      pfVar1 = *(float **)((param_1 - (int)param_4) + (int)local_78);
      iVar4 = *local_78;
      iVar3 = iVar4 + 0x800;
      iVar6 = 4;
      iVar7 = iVar8;
      do {
        *(int *)((int)local_60 + iVar7) = iVar3;
        *(int *)((int)local_40 + iVar7) = iVar3 + -0x800;
        *(int *)((int)local_20 + iVar7) = iVar3 + -0x400;
        iVar7 = iVar7 + 4;
        iVar3 = iVar3 + 0xc00;
        iVar6 = iVar6 + -1;
      } while (iVar6 != 0);
      local_70 = 4;
      iVar3 = iVar8;
      do {
        memmove(*(void **)((int)local_40 + iVar3),*(void **)((int)local_20 + iVar3),0x800);
        puVar9 = *(undefined4 **)((int)local_60 + iVar3);
        for (iVar6 = 0x100; iVar6 != 0; iVar6 = iVar6 + -1) {
          *puVar9 = 0;
          puVar9 = puVar9 + 1;
        }
        iVar3 = iVar3 + 4;
        local_70 = local_70 + -1;
      } while (local_70 != 0);
      FUN_00440b30(pfVar1,(int *)((int)local_60 + iVar8),iVar4);
      local_78 = local_78 + 1;
      local_6c = local_6c + -1;
      iVar8 = iVar7;
    } while (local_6c != 0);
  }
  if ((param_5 == 2) && (param_6 == 2)) {
    return 0xffffffff;
  }
  iVar8 = 0;
  local_6c = 0;
  if (0 < param_5) {
    iVar4 = param_2 - (int)param_3;
    iVar7 = (int)param_4 - (int)param_3;
    do {
      iVar3 = *param_3;
      iVar6 = *(int *)(iVar4 + (int)param_3);
      iVar2 = *(int *)(iVar7 + (int)param_3);
      iVar5 = FUN_00440cb0((int *)((int)local_40 + iVar8),(float *)(*(int *)(iVar3 + 0x61e8) + 0x10)
                           ,(int *)(iVar3 + 0x10));
      if (iVar5 == -1) {
        return 0xffffffff;
      }
      iVar3 = FUN_004402a0((int *)((int)local_20 + iVar8),iVar6,
                           (int *)(*(int *)(iVar3 + 0x61e8) + 0x10),iVar3 + 0x10,4,
                           (float *)(iVar2 + 0x3000));
      if (iVar3 == -1) {
        return 0xffffffff;
      }
      local_6c = local_6c + 1;
      param_3 = param_3 + 1;
      iVar8 = iVar8 + 0x10;
    } while (local_6c < param_5);
  }
  return 0;
}


// ============================
// RVA 0x414b0 -> FUN_004414b0

int __cdecl FUN_004414b0(int param_1)

{
  int iVar1;
  int extraout_ECX;
  int extraout_ECX_00;
  int extraout_EDX;
  int iVar2;
  
  iVar1 = 0;
  do {
    iVar1 = FUN_00440600(iVar1);
    if (iVar1 == -5) {
      return -1;
    }
    iVar1 = FUN_00440600(extraout_ECX);
    iVar2 = extraout_EDX;
    if (param_1 == iVar1) {
      iVar2 = extraout_ECX_00;
    }
    iVar1 = extraout_ECX_00 + 1;
  } while (iVar1 < 0x10);
  if (iVar2 < 0) {
    return -1;
  }
  return iVar2;
}


// ============================
// RVA 0x3ce60 -> FUN_0043ce60

char __cdecl FUN_0043ce60(int param_1)

{
  return (*(int *)(param_1 + 0x6180) == 1) * '\b' + '\b';
}


// ============================
// RVA 0x3ce80 -> FUN_0043ce80

int __cdecl FUN_0043ce80(int param_1)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int *piVar4;
  int iVar5;
  
  iVar3 = 0;
  iVar1 = *(int *)(param_1 + 4);
  if (0 < iVar1) {
    piVar4 = (int *)(param_1 + 0x10);
    iVar5 = iVar1;
    do {
      iVar2 = *piVar4;
      piVar4 = piVar4 + 0x10;
      iVar3 = iVar3 + iVar2;
      iVar5 = iVar5 + -1;
    } while (iVar5 != 0);
  }
  return (iVar1 + iVar3 * 3) * 3;
}


// ============================
// RVA 0x3ea90 -> FUN_0043ea90

void __cdecl FUN_0043ea90(int param_1,int *param_2,int param_3)

{
  int iVar1;
  int extraout_ECX;
  int extraout_ECX_00;
  int iVar2;
  int *piVar3;
  
  iVar2 = 0;
  if (0 < param_3) {
    do {
      iVar1 = FUN_0043cda0(iVar2);
      *param_2 = *(int *)(param_1 + 4 + ((int)(iVar1 + (iVar1 >> 0x1f & 3U)) >> 2) * 0x48);
      FUN_0043cda0(iVar2);
      iVar2 = iVar2 + 1;
      iVar1 = FUN_0043cda0(iVar2);
      if (extraout_ECX < (int)(iVar1 + (iVar1 >> 0x1f & 3U)) >> 2) {
        piVar3 = (int *)(param_1 + 4 + extraout_ECX * 0x48);
        do {
          if (*param_2 < *piVar3) {
            *param_2 = *piVar3;
          }
          piVar3 = piVar3 + 0x12;
          iVar1 = FUN_0043cda0(iVar2);
        } while (extraout_ECX_00 < (int)(iVar1 + (iVar1 >> 0x1f & 3U)) >> 2);
      }
      param_2 = param_2 + 1;
    } while (iVar2 < param_3);
  }
  return;
}


// ============================
// RVA 0x3eb30 -> FUN_0043eb30

void __cdecl FUN_0043eb30(int param_1,int param_2,int param_3)

{
  int iVar1;
  int *piVar2;
  float10 fVar3;
  
  if (0 < param_3) {
    piVar2 = (int *)(param_2 + 4);
    do {
      fVar3 = (float10)FUN_0043fd90(param_1,4);
      iVar1 = FUN_0043eb70((float)fVar3);
      *piVar2 = iVar1;
      param_1 = param_1 + 0x10;
      piVar2 = piVar2 + 0x12;
      param_3 = param_3 + -1;
    } while (param_3 != 0);
  }
  return;
}


