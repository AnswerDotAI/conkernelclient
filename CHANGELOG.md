# Release notes

<!-- do not remove -->

## 0.0.10

### New Features

- Add DeadKernelError for ZMQ socket failures with targeted exception handling ([#6](https://github.com/AnswerDotAI/conkernelclient/issues/6))


## 0.0.9

### New Features

- Fix concurrent execute races: fail-fast on channel stop/kernel death, abort pending on kernel error, add `stop_on_error` support ([#5](https://github.com/AnswerDotAI/conkernelclient/issues/5))


## 0.0.7

### New Features

- Add `stdin_send` ([#4](https://github.com/AnswerDotAI/conkernelclient/issues/4))


## 0.0.5

### Bugs Squashed

- Fix race conditions in channel start/stop and add reader error logging ([#3](https://github.com/AnswerDotAI/conkernelclient/issues/3))


## 0.0.4

### New Features

- Ensure shell reader task is fully started before returning from `start_channels` ([#2](https://github.com/AnswerDotAI/conkernelclient/issues/2))


## 0.0.3

- Add readme


## 0.0.2

### New Features

- Remove subshell stuff ([#1](https://github.com/AnswerDotAI/conkernelclient/issues/1))


## 0.0.1

- Init release

