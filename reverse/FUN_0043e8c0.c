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
