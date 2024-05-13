main:
	./frpc -c frpc.toml > /dev/zero
visitor:
	./frpc -c frpc_visitor.toml > /dev/zero
