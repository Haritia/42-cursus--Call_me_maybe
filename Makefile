UV = uv run
FLAGS = 

%:
	@:

ARGS = $(filter-out run,$(MAKECMDGOALS))

install:
	uv sync

run:
	$(UV) python -m src $(ARGS)

debug: