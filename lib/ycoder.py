
try:
    import yaml

    def encode(data):
        return yaml.dump(data, default_flow_style=False,
                              Dumper=yaml.CSafeDumper)

    def decode(stream):
        return yaml.load(stream, Loader=yaml.CSafeLoader)

except ImportError:
    import yaml_slow as yaml

    def encode(data):
        return yaml.safe_dump(data, default_flow_style=False)

    def decode(stream):
        return yaml.safe_load(stream)
