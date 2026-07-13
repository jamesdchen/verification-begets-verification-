meta:
  id: g_enum_006
  endian: be
seq:
  - id: kind_field
    type: u1
    enum: kind
  - id: f0
    type: u4
  - id: f1
    type: u8
  - id: f2
    type: u4
enums:
  kind:
    64: v64
    79: v79
    161: v161
