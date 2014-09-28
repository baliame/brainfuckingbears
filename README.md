brainfuckingbears
=================

An open-source brainfuck-like coding language. Contains an interpreter written in Python and example code.

Created for the 43rd Schönherz Cup by Ákos Tóth and other contributors.

<strong>Usage:</strong>
```bash
python3 bfb.py FILE [debug|slow|veryslow] [track] [breakpoint position]
```

<strong>Explanation:</strong>
<ul>
<li>debug: start immediately in the debug menu, where you can switch to 'slow' or 'veryslow' mode, or proceed step-by-step.<br />
In the debug menu, you have the option to view the event log (e), recorded only if tracking, or to view the memory (m).</li>
<li>slow: execute normally with a 100 ms delay between instructions.</li>
<li>veryslow: execute normally with a 1 s delay between instructions.<br />
Debug, slow and very slow (by nature) are mutually exclusive.</li>
<li>track: if set, event log is recording. The interpreter will use significantly more memory and CPU time.</li>
<li>breakpoint position: when execution hits the character at the specified position, the debug menu will open.</li>


Like our Facebook page:
https://www.facebook.com/bigfluffybears
