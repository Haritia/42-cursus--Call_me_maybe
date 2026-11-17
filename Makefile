UV = uv run

FLAGS = --warn-return-any\
		--warn-unused-ignores\
		--ignore-missing-imports\
		--disallow-untyped-defs\
		--check-untyped-defs

VENV = .venv

LLM = llm_sdk

%:
	@:

ARGS = $(filter-out run,$(MAKECMDGOALS))

install:
	uv sync

run:
	$(UV) python -m src $(ARGS)

lint:
	$(UV) flake8 --docstring google  --exclude=$(LLM),$(VENV) .
	$(UV) mypy --exclude=$(LLM) --exclude=$(VENV) $(FLAGS) .

lint-strict:
	$(UV) flake8 --docstring google  --exclude=$(LLM),$(VENV) .
	$(UV) mypy --strict --exclude=$(LLM) --exclude=$(VENV) .

debug:
	$(UV) python -m pdp src $(ARGS)

clean:
	find . | grep "__pycache__" | xargs -I {} rm -rf {}
	find . -name ".mypy_cache" -type d | xargs rm -rf
	rm -rf $(VENV)

.PHONY: install run debug lint lint-strict clean