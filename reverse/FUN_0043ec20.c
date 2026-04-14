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
