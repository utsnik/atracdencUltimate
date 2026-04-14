// Function: FUN_00404d20 @ 0x404d20

int __cdecl
FUN_00404d20(int param_1,short *param_2,undefined4 *param_3,uint param_4,undefined4 *param_5)

{
  undefined4 *puVar1;
  uint uVar2;
  int iVar3;
  int iVar4;
  
  puVar1 = param_5;
  if (*(int *)(param_1 + 0x90) != 0x10) {
    *(undefined4 *)(param_1 + 0xc) = 0x10e;
    *param_5 = 0;
    return -0x80000000;
  }
  if (*(int *)(param_1 + 0x28) == 0) {
    uVar2 = FUN_00436ce0(*(int *)(param_1 + 0x34),param_2,param_3,&param_4,param_5);
    iVar3 = FUN_00404520(param_1,uVar2);
    if (iVar3 < 0) {
      *puVar1 = 0;
      return iVar3;
    }
    iVar4 = 0;
    if (iVar3 != 0) {
      iVar4 = iVar3;
    }
    return iVar4;
  }
  if (*(int *)(param_1 + 0x28) != 1) {
    *(undefined4 *)(param_1 + 0xc) = 0x117;
    *param_5 = 0;
    return -0x80000000;
  }
  uVar2 = 0;
  if (param_4 != 0) {
    do {
      *(ushort *)(uVar2 + (int)param_2) =
           CONCAT11(*(undefined1 *)(uVar2 + 1 + (int)param_2),*(undefined1 *)(uVar2 + (int)param_2))
      ;
      uVar2 = uVar2 + 2;
    } while (uVar2 < param_4);
  }
  uVar2 = FUN_0043c5d0(param_2,param_3,*(undefined4 **)(param_1 + 0x4c),param_4 >> 1,2,
                       *(undefined4 *)(param_1 + 0x50));
  puVar1 = param_5;
  if (*(int *)(param_1 + 0x50) < 1) {
    *param_5 = 0;
  }
  else {
    *param_5 = *(undefined4 *)(param_1 + 0x38);
  }
  if (uVar2 == 1) {
    *(undefined4 *)(param_1 + 0xc) = 0xb;
    *(int *)(param_1 + 0x50) = *(int *)(param_1 + 0x50) + 1;
    return 1;
  }
  iVar3 = FUN_00404520(param_1,uVar2);
  if (iVar3 < 0) {
    *puVar1 = 0;
    return iVar3;
  }
  iVar4 = 0;
  if (iVar3 != 0) {
    iVar4 = iVar3;
  }
  *(int *)(param_1 + 0x50) = *(int *)(param_1 + 0x50) + 1;
  return iVar4;
}


