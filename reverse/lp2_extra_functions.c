// ============================
// RVA 0x3ec20 -> FUN_0043ec20

char __cdecl FUN_0043ec20(int param_1)

{
  if (param_1 < 8) {
    return '\0';
  }
  if (param_1 < 0xc) {
    return '\x01';
  }
  if (param_1 < 0x10) {
    return '\x02';
  }
  if (param_1 < 0x14) {
    return '\x03';
  }
  return (0x19 < param_1) + '\x04';
}


// ============================
// RVA 0x3e710 -> FUN_0043e710

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

float10 __cdecl FUN_0043e710(int param_1)

{
  if ((-1 < param_1) && (param_1 < 0x40)) {
    return (float10)(float)(&DAT_0048eae8)[param_1];
  }
  return (float10)_DAT_0048ebe4 * (float10)_DAT_00491128;
}


// ============================
// RVA 0x3e9b0 -> FUN_0043e9b0

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int __cdecl
FUN_0043e9b0(int param_1,int param_2,float param_3,int param_4,int param_5,int *param_6,int param_7)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int *piVar5;
  
  iVar4 = param_2;
  if (param_2 == 0) {
    return 0;
  }
  iVar1 = FUN_0043e740(param_2);
  if (0 < param_4) {
    param_2 = param_4;
    piVar5 = param_6;
    do {
      if (param_3 <= ABS(*(float *)((param_5 - (int)param_6) + (int)piVar5))) {
        iVar2 = ftol();
        iVar3 = iVar2 + -0x1f;
        if (iVar1 < iVar2 + -0x1f) {
          iVar3 = iVar1;
        }
        if (iVar3 < -iVar1) {
          iVar3 = -iVar1;
        }
        *piVar5 = iVar3;
      }
      else {
        *piVar5 = 0;
      }
      piVar5 = piVar5 + 1;
      param_2 = param_2 + -1;
    } while (param_2 != 0);
  }
  iVar4 = FUN_0043fdd0(iVar4 * 0x30 + *(int *)(*(int *)(param_7 + 0x24) + param_1 * 4),(int)param_6,
                       param_4);
  if (iVar4 != -0x8000) {
    return iVar4 + 6;
  }
  return -0x8000;
}


// ============================
// RVA 0x3ebd0 -> FUN_0043ebd0

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

float10 __cdecl FUN_0043ebd0(int param_1,int param_2)

{
  if (param_1 == 0) {
    return (float10)_DAT_0048b42c;
  }
  if (param_1 < 0) {
    return (float10)DAT_0048ec68 / (float10)*(float *)(&DAT_0048ec9c + param_2 * 4);
  }
  if (0xc < param_1) {
    param_1 = 0xc;
  }
  return (float10)(&DAT_0048ec68)[param_1] / (float10)*(float *)(&DAT_0048ec9c + param_2 * 4);
}


// ============================
// RVA 0x40600 -> FUN_00440600

undefined4 __cdecl FUN_00440600(int param_1)

{
  if ((-1 < param_1) && (param_1 < 0x10)) {
    return *(undefined4 *)(&DAT_0048eaa8 + param_1 * 4);
  }
  return 0xfffffffb;
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
// RVA 0x3e8c0 -> FUN_0043e8c0

undefined4 __cdecl
FUN_0043e8c0(int param_1,int *param_2,int param_3,int param_4,int param_5,int *param_6,int param_7,
            int param_8,int param_9,int param_10)

{
  int iVar1;
  int *piVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  float10 fVar7;
  int iVar8;
  int local_4;
  
  iVar4 = 0;
  iVar6 = 0;
  local_4 = 0;
  if (0 < param_7) {
    iVar1 = param_9 - (int)param_2;
    iVar5 = param_5 - (int)param_2;
    do {
      piVar2 = (int *)(iVar1 + (int)param_2);
      if (*(int *)((int)piVar2 + (param_1 - param_9)) == 1) {
        fVar7 = FUN_0043ebd0(*piVar2,*param_2);
        iVar8 = param_10;
        iVar4 = FUN_0043cda0(iVar6);
        piVar2 = (int *)(param_4 + iVar4 * 4);
        iVar4 = FUN_0043cda0(iVar6);
        iVar4 = param_3 + iVar4 * 4;
        iVar3 = FUN_0043d130(iVar6);
        iVar4 = FUN_0043e9b0(param_8,*param_2,(float)fVar7,iVar3,iVar4,piVar2,iVar8);
        *(int *)(iVar5 + (int)param_2) = iVar4;
        if (iVar4 == -0x8000) {
          return 0xffff8000;
        }
      }
      piVar2 = (int *)(iVar5 + (int)param_2);
      param_2 = param_2 + 1;
      iVar4 = local_4 + *piVar2;
      iVar6 = iVar6 + 1;
      local_4 = iVar4;
    } while (iVar6 < param_7);
  }
  *param_6 = iVar4;
  return 0;
}


// ============================
// RVA 0x3e7a0 -> FUN_0043e7a0

int __cdecl
FUN_0043e7a0(int param_1,int param_2,undefined4 param_3,int *param_4,int *param_5,int param_6,
            int param_7)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int *piVar5;
  int iVar6;
  
  iVar4 = param_6;
  piVar5 = param_5;
  if (0 < param_6) {
    do {
      iVar1 = ftol();
      *piVar5 = iVar1;
      if (param_7 < iVar1) {
        *piVar5 = param_7;
      }
      if (*piVar5 < param_2) {
        *piVar5 = param_2;
      }
      iVar4 = iVar4 + -1;
      piVar5 = piVar5 + 1;
    } while (iVar4 != 0);
  }
  iVar1 = 1;
  iVar4 = 0;
  if (1 < param_6) {
    do {
      if (iVar4 < param_4[iVar1]) {
        iVar4 = param_4[iVar1];
      }
      iVar1 = iVar1 + 1;
    } while (iVar1 < param_6);
    if (0x1d < iVar4) {
      iVar4 = 6;
      goto LAB_0043e843;
    }
  }
  iVar4 = ftol();
  if (iVar4 == 0) {
    iVar4 = 1;
  }
LAB_0043e843:
  iVar1 = 0;
  if (param_6 < 1) {
    return iVar4;
  }
  iVar3 = (int)param_5 - (int)param_4;
  do {
    if (*param_4 < iVar4) {
      *(undefined4 *)(iVar3 + (int)param_4) = 0;
    }
    iVar2 = 0;
    piVar5 = param_4;
    iVar6 = iVar1;
    do {
      iVar6 = iVar6 + -1;
      piVar5 = piVar5 + -1;
      if ((-1 < iVar6) && (*param_4 < *piVar5 - *(int *)(param_1 + iVar2 * 4))) {
        param_5[iVar1] = 0;
      }
      iVar2 = iVar2 + 1;
    } while (iVar2 < 8);
    iVar1 = iVar1 + 1;
    param_4 = param_4 + 1;
  } while (iVar1 < param_6);
  return iVar4;
}


