import typing as t

from pytoniq_core import (
    ConfigParam,
    Builder,
    Slice,
    HashMap,
)


def parse_config(config_slice: Slice) -> dict[int, t.Any]:
    def key_deserializer(src: t.Any) -> int:
        return Builder().store_bits(src).to_slice().load_int(32)

    def value_deserializer(src: Slice) -> Slice:
        return src.load_ref().begin_parse()

    config_map = HashMap.parse(
        dict_cell=config_slice,
        key_length=32,
        key_deserializer=key_deserializer,
        value_deserializer=value_deserializer,
    )

    params_by_id = ConfigParam.params
    out: t.Dict[int, t.Any] = {}

    for key_id, raw_value_slice in config_map.items():
        param = params_by_id.get(key_id)
        if param is not None:
            out[key_id] = param.deserialize(raw_value_slice)
        else:
            out[key_id] = raw_value_slice

    return out
