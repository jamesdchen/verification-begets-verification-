meta:
  id: e_lenprefix_006
  endian: le
seq:
  - id: f0
    type: u4
  - id: len_data
    type: u1
  - id: data
    type: str
    size: len_data
    encoding: ASCII
