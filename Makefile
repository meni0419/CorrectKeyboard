.PHONY: push merge_master delete_branch

# Detect Windows or Unix-like system
ifeq ($(OS), Windows_NT)
	SHELL := cmd
	DEL_CMD := if not defined
	EXIT_CMD := exit /b
	CURRENT_BRANCH_CMD := for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD') do set current_branch=%%b
else
	SHELL := /bin/bash
	DEL_CMD := test -z
	EXIT_CMD := exit
	CURRENT_BRANCH_CMD := current_branch=$(shell git rev-parse --abbrev-ref HEAD)
endif

# Push command
push:
ifeq ($(OS), Windows_NT)
	@if not defined c ( \
		echo Usage: make push c="<comment>"; \
		exit /b 1; \
	) else ( \
		for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD') do set current_branch=%%b && \
		git add . && \
		git commit -m "$(c)" && \
		git push origin %%b \
	)
else
	@if [ -z "$(c)" ]; then \
		echo "Usage: make push c=\"<comment>\""; \
		exit 1; \
	fi; \
	current_branch=$$(git rev-parse --abbrev-ref HEAD) && \
	git add . && \
	git commit -m "$(c)" && \
	git push origin $$current_branch
endif

# Merge to master command
merge_master:
ifeq ($(OS), Windows_NT)
	for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD') do set current_branch=%%b ^ \
		&& git checkout master ^ \
		&& git merge %%b -m "Merged %%b into master" ^ \
		&& git push ^ \
		&& git checkout %%b
else
	current_branch=$$(git rev-parse --abbrev-ref HEAD) && \
	git checkout master && \
	git merge $$current_branch -m "Merged $$current_branch into master" && \
	git push && \
	git checkout $$current_branch
endif

# Delete branch command
delete_branch:
ifeq ($(OS), Windows_NT)
	@if not defined b ( \
		echo Usage: make delete_branch b=<branch>; \
		exit /b 1; \
	) else ( \
		git branch -d $(b) || git branch -D $(b) && \
		git push origin --delete $(b) \
	)
else
	@if [ -z "$(b)" ]; then \
		echo "Usage: make delete_branch b=<branch>"; \
		exit 1; \
	fi; \
	git branch -d $(b) || git branch -D $(b) && \
	git push origin --delete $(b)
endif

# Create repository
create_repository:
ifeq ($(OS), Windows_NT)
	@if not defined r ( \
		echo "Usage: make create_repository r=name_rep"; \
		exit /b 1; \
	) else ( \
		git init && \
		git add . && \
		git commit -m "Initial commit" && \
		gh auth login && \
		gh repo create $(r) --public --source=. --remote=origin && \
		git push origin master
	)
else
	@if [ -z "$(r)" ]; then \
		echo "Usage: make create_repository r=name_rep "; \
		exit 1; \
	fi; \
	git init && \
	git add . && \
	git commit -m "Initial commit" && \
	gh auth login && \
	gh repo create $(r) --public --source=. --remote=origin && \
	git push origin master
endif