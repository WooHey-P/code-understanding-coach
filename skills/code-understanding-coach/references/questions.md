# Writing questions

A good question can only be answered by someone who holds a working model of the code.
The developer has the code open, so anything answerable by finding and copying one or
two lines is too easy.

## Shape of a question message

```text
<Area> — <one or two lines of context and the conditions that matter>

<The question: what happens in this concrete situation, and why?>

Start from: <path:line of the entry point>
```

One question per message, asking for **one** prediction and its reason. "What status
does it return, how many attempts are left, and is anything saved?" is three questions;
keep the one that best tests the idea. Nothing after it: no answer, no hints list, no
"next I will ask".

## What to ask about

- **Predict an outcome in a concrete scenario the code does not spell out.** "A job
  times out on its first try and succeeds on the retry. How many times does the
  completion webhook fire? Why?"
- **Failure and boundary behavior.** What happens when a dependency fails, a value is
  missing, a limit is reached, or a step runs twice.
- **Effects across modules.** A change of state in one place and what another part of
  the system then observes.
- **Reversal.** "If this check moved after the save instead of before it, what would
  break?"
- **Ordering and concurrency,** when the code makes them matter. "Two workers pick up
  the same queued job at the same moment. What can happen?"

## What not to ask

| Avoid | Why | Ask instead |
|---|---|---|
| "What is the name of the function that parses dates?" | Trivia; a search answers it | "A cached price is one second past its TTL. What does the next request return, and where is that decided?" |
| "What is `MAX_RETRIES` set to?" | Copying a constant | "How many times is a job attempted when every attempt times out, and does a non-timeout error change that?" (only if the retry logic makes it non-obvious) |
| "Why is the override unaffected?" | Gives away that it is unaffected | "Does the override still apply after this change? Why?" |
| "Why did the authors choose a message queue?" | Intent cannot be read from code | "What happens to queued jobs if the worker crashes mid-job?" |
| A question that bundles three questions | Hard to grade, overwhelming | Pick the one that matters most |
| A question whose premise you have not checked | A wrong premise wastes their time and your credibility | Trace the code first |

## Settle the minimum answer before asking

Privately, before sending, decide:

1. **Outcome** — the observable result in the scenario, as short as possible.
2. **Cause** — the one causal relationship that explains it.
3. **Evidence** — the lines that establish both.

Only the outcome and the cause are required to count as understood. Your fuller
explanation can mention more, but extra details are not extra requirements. Do not show
any of this until after grading.

Then check:

- The premise is true in the current code.
- The stated conditions are enough for one defensible answer; add a condition if two
  answers could both be right.
- The wording does not reveal the outcome.
- Someone could not answer by copying a single line.

## Starting point

Give the entry point, not the answer. Good: the route handler or public function where
the scenario begins. Bad: the line with the comparison that decides the outcome.

## Difficulty

- **Default (mixed):** alternate between outside behavior (what users or callers see,
  failures, module interactions) and inside logic (which branch runs for an input, how
  state or ordering behaves).
- **Easier:** single-module behavior with one condition.
- **Deeper:** cross-module effects, failure recovery, ordering, or reversal questions.

Change difficulty when the developer asks, or after two misconceptions in a row on
basics.

## Transfer questions

After a misconception or an explanation request, ask about the same concept in a new
situation: change the input, the order of events, or where it happens. It must require
applying the idea, not finding the explanation you just gave. Label hypothetical
conditions as hypothetical; do not pretend the code contains something it does not.
