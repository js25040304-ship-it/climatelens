"""Plain-language interpretation of server-calculated evidence."""
import math


def explanation(r):
 """Plain-language summary of server statistics only. Interval endpoints are scaled to per-decade like the slope; numbers never use scientific notation."""
 if not r or not r.get('stats'): return 'No valid trend inference is available. Record the data limitation; do not infer a trend from missing evidence.'
 s=r['stats']; slope=s['slope_decade']; lo,hi=(v*10 for v in s['ci95_year']); unit={'C':'°C'}.get(r['unit'],r['unit']); p=s['p_value']
 biggest=max(abs(slope),abs(lo),abs(hi)); digits=max(0,2-math.floor(math.log10(biggest))) if biggest else 0
 def num(v): return f'{v+0.:,.{digits}f}'
 period=f"{r['settings']['start']}–{r['settings']['end']}" if r.get('settings') else 'the selected period'
 # Keep the displayed p-value on the same side of 0.05 as the test decision.
 p_text = format(p, '.3g')
 if (float(p_text) < 0.05) != (p < 0.05):
  p_text = str(p)
 move={'increasing':'rises','decreasing':'falls'}.get(s['direction'],'stays flat')
 return (f"Over {period} ({s['n']} complete years), the fitted straight line {move} by about {num(abs(slope))} {unit} every 10 years. "
  f"95% confidence interval: {num(lo)} to {num(hi)} {unit} per decade, a plausible range for the underlying rate. "
  +('p < 0.001' if p<.001 else f'p = {p_text}')+': '
  +(f"if there were no linear trend, a test statistic at least this extreme in either direction would be unlikely, so this is evidence of a {'rise' if slope>0 else 'fall'} at the 0.05 level. " if s['significant'] else 'the interval includes zero, so zero change is still consistent with the data at the 0.05 level. This is not proof that nothing changed; a change may be too small or too noisy to detect in these years. ')
  +'This describes a pattern in observational data; it does not show what caused it.')
