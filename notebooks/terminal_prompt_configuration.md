# Terminal Prompt Configuration

This guide explains how to configure your terminal prompt to show both the current Git branch and Python virtual environment.

## Bash Configuration

Add the following to your `~/.bashrc` or `~/.bash_profile`:

```bash
# Show git branch in prompt
parse_git_branch() {
    git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ (\1)/'
}

# Show virtual environment name if active
show_virtual_env() {
    if [ -n "$VIRTUAL_ENV" ]; then
        echo "($(basename $VIRTUAL_ENV))"
    fi
}

# Set the prompt
export PS1='$(show_virtual_env)\w\[\033[32m\]$(parse_git_branch)\[\033[00m\] $ '
```

## What Each Part Does

### 1. Git Branch Function
```bash
parse_git_branch() {
    git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ (\1)/'
}
```
- Gets the current git branch
- Formats it to show just the branch name in parentheses
- Silently fails if not in a git repository

### 2. Virtual Environment Function
```bash
show_virtual_env() {
    if [ -n "$VIRTUAL_ENV" ]; then
        echo "($(basename $VIRTUAL_ENV))"
    fi
}
```
- Detects if a Python virtual environment is active
- Shows the environment name in parentheses if active
- Shows nothing if no environment is active

### 3. Prompt Configuration
```bash
export PS1='$(show_virtual_env)\w\[\033[32m\]$(parse_git_branch)\[\033[00m\] $ '
```
- `$(show_virtual_env)`: Shows virtual environment if active
- `\w`: Current working directory
- `\[\033[32m\]`: Sets text color to green
- `$(parse_git_branch)`: Shows git branch in green
- `\[\033[00m\]`: Resets text color

## Example Outputs

- With virtual env and git: `(venv) ~/projects/repo (main) $`
- With git only: `~/projects/repo (main) $`
- With virtual env only: `(venv) ~/projects $`
- Basic: `~ $`

## Activating Changes
After adding to your bash config file, either:
1. Restart your terminal, or
2. Run `source ~/.bashrc` (or `source ~/.bash_profile` if that's where you added it)
