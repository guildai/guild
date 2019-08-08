# Time range spec

## Lexer

    >>> from guild.timerange import trlex
    >>> lexer = trlex.lexer()

    >>> def tokens(s):
    ...     lexer.input(s)
    ...     while True:
    ...         tok = lexer.token()
    ...         if not tok:
    ...             break
    ...         print(tok)

    >>> tokens("")

Numbers:

    >>> tokens("1")
    LexToken(NUMBER,1,1,0)

    >>> tokens("2 3 4")
    LexToken(NUMBER,2,1,0)
    LexToken(NUMBER,3,1,2)
    LexToken(NUMBER,4,1,4)

Dates:

    >>> tokens("2019-10-31")
    LexToken(DATETIME,(2019, 10, 31),1,0)

    >>> tokens("19-11-30")
    LexToken(DATETIME,(2019, 11, 30),1,0)

    >>> tokens("12-31")
    LexToken(DATETIME,(20..., 12, 31),1,0)

    >>> tokens("9-8")
    LexToken(DATETIME,(20..., 9, 8),1,0)

    >>> tokens("1-31")
    LexToken(DATETIME,(2019, 1, 31),1,0)

    >>> tokens("1-32")
    Traceback (most recent call last):
    ValueError: invalid date '1-32'

    >>> tokens("2018-13-01")
    Traceback (most recent call last):
    ValueError: invalid date '2018-13-01'

Times:

    >>> tokens("11:10")
    LexToken(TIME,(11, 10),1,0)

    >>> tokens("0:00")
    LexToken(TIME,(0, 0),1,0)

    >>> tokens("1:00")
    LexToken(TIME,(1, 0),1,0)

    >>> tokens("1:2")
    LexToken(TIME,(1, 2),1,0)

    >>> tokens("13:30")
    LexToken(TIME,(13, 30),1,0)

    >>> tokens("23:59")
    LexToken(TIME,(23, 59),1,0)

    >>> tokens("24:00")
    Traceback (most recent call last):
    ValueError: invalid time '24:00'

    >>> tokens("000:0")
    Traceback (most recent call last):
    ValueError: invalid time '000:0'

Units:

    >>> tokens("minutes hours days weeks months years")
    LexToken(MINUTE,'minutes',1,0)
    LexToken(HOUR,'hours',1,8)
    LexToken(DAY,'days',1,14)
    LexToken(WEEK,'weeks',1,19)
    LexToken(MONTH,'months',1,25)
    LexToken(YEAR,'years',1,32)

    >>> tokens("minute hour day week month year")
    LexToken(MINUTE,'minute',1,0)
    LexToken(HOUR,'hour',1,7)
    LexToken(DAY,'day',1,12)
    LexToken(WEEK,'week',1,16)
    LexToken(MONTH,'month',1,21)
    LexToken(YEAR,'year',1,27)

    >>> tokens("MINutes houR DaY WEEKs MONths yeARs")
    LexToken(MINUTE,'MINutes',1,0)
    LexToken(HOUR,'houR',1,8)
    LexToken(DAY,'DaY',1,13)
    LexToken(WEEK,'WEEKs',1,17)
    LexToken(MONTH,'MONths',1,23)
    LexToken(YEAR,'yeARs',1,30)

Other reserved:

    >>> tokens("today yesterday this last ago before after between and")
    LexToken(TODAY,'today',1,0)
    LexToken(YESTERDAY,'yesterday',1,6)
    LexToken(THIS,'this',1,16)
    LexToken(LAST,'last',1,21)
    LexToken(AGO,'ago',1,26)
    LexToken(BEFORE,'before',1,30)
    LexToken(AFTER,'after',1,37)
    LexToken(BETWEEN,'between',1,43)
    LexToken(AND,'and',1,51)

    >>> tokens("toDaY yesTERday thIS LAsT AGO beFoRE AFTer betWEEn AND")
    LexToken(TODAY,'toDaY',1,0)
    LexToken(YESTERDAY,'yesTERday',1,6)
    LexToken(THIS,'thIS',1,16)
    LexToken(LAST,'LAsT',1,21)
    LexToken(AGO,'AGO',1,26)
    LexToken(BEFORE,'beFoRE',1,30)
    LexToken(AFTER,'AFTer',1,37)
    LexToken(BETWEEN,'betWEEn',1,43)
    LexToken(AND,'AND',1,51)

Expressions:

    >>> tokens("after 5 minutes ago")
    LexToken(AFTER,'after',1,0)
    LexToken(NUMBER,5,1,6)
    LexToken(MINUTE,'minutes',1,8)
    LexToken(AGO,'ago',1,16)

    >>> tokens("before this week")
    LexToken(BEFORE,'before',1,0)
    LexToken(THIS,'this',1,7)
    LexToken(WEEK,'week',1,12)

    >>> tokens("between 1 and 3 hours ago")
    LexToken(BETWEEN,'between',1,0)
    LexToken(NUMBER,1,1,8)
    LexToken(AND,'and',1,10)
    LexToken(NUMBER,3,1,14)
    LexToken(HOUR,'hours',1,16)
    LexToken(AGO,'ago',1,22)

    >>> tokens("between 5-1 and 5-31")
    LexToken(BETWEEN,'between',1,0)
    LexToken(DATETIME,(20..., 5, 1),1,8)
    LexToken(AND,'and',1,12)
    LexToken(DATETIME,(20..., 5, 31),1,16)

Invalid:

    >>> tokens("a")
    Traceback (most recent call last):
    SyntaxError: unexpected 'a' at position 0

    >>> tokens("aftr last week")
    Traceback (most recent call last):
    SyntaxError: unexpected 'aftr' at position 0

    >>> tokens("after the equinox")
    Traceback (most recent call last):
    SyntaxError: unexpected 'the' at position 6

    >>> tokens("yearsss")
    Traceback (most recent call last):
    SyntaxError: unexpected 'ss' at position 5

    >>> tokens("2015-01-03-01")
    Traceback (most recent call last):
    SyntaxError: unexpected '-01' at position 10

## Parser

The time range parser generates a function that returns a tuple of
start and end times for a reference time. The function can be used to
implement a filter for a time range by matching times greater than or
equal to start and less than end.

Let's first create a parser:

    >>> from guild.timerange import trparse
    >>> parser = trparse.parser()

Next we'll create a helper function that applies a time range spec to
a reference time and prints the start and end times.

    >>> def apply(s, ref):
    ...     f = parser.parse(s)
    ...     start, end = f(ref)
    ...     print("ref:   %s" % ref)
    ...     print("start: %s" % start)
    ...     print("end:   %s" % end)

Here's a reference date for our core tests:

    >>> from datetime import datetime
    >>> ref = datetime(2019, 5, 1, 14, 35, 23)

### Unit periods

Unit periods are specs that imply a period of time that is defined by
a specified unit. Unites include minutes, hours, days, weeks, months,
and years.

Periods can be specified using special keywords "this" and "last",
indicating the period that falls within the reference time and the
period that occurs just prior to the reference time respectively. For
example, "this hour" indicates that the period should fall within the
reference time hour as defined by the period "00:00" and
"00:59". Similarly, "last hour" secifies the period in the hour prior
to the reference time.

Periods can also be specified using the syntax "N <unit(s)> ago". For
example, "1 hour ago" specifies the period of one hour occuring prior
to the reference time hour start.

Below are examples applied to our reference time.

Minute periods:

    >>> apply("this minute", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 14:35:00
    end:   2019-05-01 14:36:00

    >>> apply("last minute", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 14:34:00
    end:   2019-05-01 14:35:00

    >>> apply("1 minute ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 14:34:00
    end:   2019-05-01 14:35:00

    >>> apply("5 minutes ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 14:30:00
    end:   2019-05-01 14:31:00

Hour periods:

    >>> apply("this hour", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 14:00:00
    end:   2019-05-01 15:00:00

    >>> apply("last hour", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 13:00:00
    end:   2019-05-01 14:00:00

    >>> apply("1 hour ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 13:00:00
    end:   2019-05-01 14:00:00

    >>> apply("5 hours ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 09:00:00
    end:   2019-05-01 10:00:00

    >>> apply("24 hours ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-30 14:00:00
    end:   2019-04-30 15:00:00

Day periods:

    >>> apply("today", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 00:00:00
    end:   2019-05-02 00:00:00

    >>> apply("yesterday", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-30 00:00:00
    end:   2019-05-01 00:00:00

    >>> apply("1 day ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-30 00:00:00
    end:   2019-05-01 00:00:00

    >>> apply("2 days ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-29 00:00:00
    end:   2019-04-30 00:00:00

    >>> apply("10 days ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-21 00:00:00
    end:   2019-04-22 00:00:00

Week periods:

    >>> apply("this week", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-29 00:00:00
    end:   2019-05-06 00:00:00

    >>> apply("last week", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-22 00:00:00
    end:   2019-04-29 00:00:00

    >>> apply("1 week ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-22 00:00:00
    end:   2019-04-29 00:00:00

    >>> apply("2 weeks ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-15 00:00:00
    end:   2019-04-22 00:00:00

    >>> apply("10 weeks ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-02-18 00:00:00
    end:   2019-02-25 00:00:00

Month periods:

    >>> apply("this month", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 00:00:00
    end:   2019-05-31 00:00:00

    >>> apply("last month", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-01 00:00:00
    end:   2019-04-30 00:00:00

    >>> apply("1 month ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-01 00:00:00
    end:   2019-04-30 00:00:00

    >>> apply("3 months ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-02-01 00:00:00
    end:   2019-02-28 00:00:00

    >>> apply("15 months ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2018-02-01 00:00:00
    end:   2018-02-28 00:00:00

    >>> apply("39 months ago", ref)  # leap year
    ref:   2019-05-01 14:35:23
    start: 2016-02-01 00:00:00
    end:   2016-02-29 00:00:00

Year periods:

    >>> apply("this year", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-01-01 00:00:00
    end:   2020-01-01 00:00:00

    >>> apply("last year", ref)
    ref:   2019-05-01 14:35:23
    start: 2018-01-01 00:00:00
    end:   2019-01-01 00:00:00

    >>> apply("1 year ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2018-01-01 00:00:00
    end:   2019-01-01 00:00:00

    >>> apply("5 years ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2014-01-01 00:00:00
    end:   2015-01-01 00:00:00