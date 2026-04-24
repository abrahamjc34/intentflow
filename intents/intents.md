# IntentFlow Intents

Each `## section` below defines one intent: the keywords that trigger it,
example phrases, the tool to call, and (optionally) which argument to extract.

## calculator
keywords: calculate, math, compute, plus, minus, times, divided, multiply, +, -, *, /
examples:
  - what is 5 + 3
  - calculate 100 / 4
  - 25 times 40
tool: calculator
extract: expression

## current_time
keywords: time, date, now, today, clock, what day
examples:
  - what time is it
  - what is the current date
  - today
tool: current_time

## greet
keywords: hello, hi, hey, greet, welcome
examples:
  - say hi to alice
  - greet bob
  - hello
tool: greet
extract: name

## reverse
keywords: reverse, backward, flip, mirror
examples:
  - reverse hello world
  - flip this text
tool: reverse
extract: text

## word_count
keywords: word count, count words, how many words, number of words
examples:
  - count words in hello world from mars
  - how many words in this sentence
tool: word_count
extract: text

## list_tools
keywords: list tools, what can you do, help, commands, abilities, tools
examples:
  - what can you do
  - list tools
  - help
tool: list_tools
