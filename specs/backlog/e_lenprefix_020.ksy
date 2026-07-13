meta:
  id: e_lenprefix_020
  endian: be
seq:
  - id: f0
    type: u8
  - id: len_data
    type: u1
  - id: data
    type: str
    size: len_data
    encoding: ASCII
