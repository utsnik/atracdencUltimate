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
