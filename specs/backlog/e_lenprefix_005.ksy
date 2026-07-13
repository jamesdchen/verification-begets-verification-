meta:
  id: e_lenprefix_005
  endian: be
seq:
  - id: f0
    type: u4
  - id: len_data
    type: u2
  - id: data
    type: str
    size: len_data
    encoding: ASCII
