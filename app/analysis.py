"""OLS slope, Newey-West covariance, approximate t inference."""
import math
def analyze(rows):
 import numpy as np
 import statsmodels.api as sm
 if len(rows)<10: raise ValueError('Fewer than 10 complete years. No trend inference is produced.')
 years=np.array([r['year'] for r in rows],dtype=float)
 if not np.all(np.diff(years)==1): raise ValueError('Incomplete years create gaps. Select a contiguous complete period for HAC inference.')
 values=np.array([r['value'] for r in rows],dtype=float)
 if not np.all(np.isfinite(values)): raise ValueError('Non-finite observations.')
 if np.ptp(values)<1e-12: raise ValueError('Constant observations: variance-based inference is undefined.')
 x=sm.add_constant(years-years[0]); n=len(rows)
 lag=min(n-3,max(1,int(math.floor(4*(n/100)**(2/9)))))
 fit=sm.OLS(values,x).fit(cov_type='HAC',cov_kwds={'maxlags':lag,'use_correction':True},use_t=True)
 # Residuals at floating-point noise level cannot estimate a HAC variance.
 tolerance = 16 * np.finfo(float).eps * np.max(np.abs(values))
 if np.max(np.abs(fit.resid)) <= tolerance or not np.isfinite(fit.bse[1]) or fit.bse[1] <= 0:
  raise ValueError('Residual variation is too small to estimate trend uncertainty.')
 slope=float(fit.params[1]); ci=fit.conf_int(alpha=.05)[1].tolist(); p=float(fit.pvalues[1])
 if not all(math.isfinite(v) for v in [slope,p,*ci]): raise ValueError('The uncertainty estimate is degenerate.')
 return {'n':n,'slope_year':slope,'slope_decade':slope*10,'ci95_year':ci,'p_value':p,'significant':p<.05,'direction':'increasing' if slope>0 else 'decreasing' if slope<0 else 'flat','hac_lags':lag,'fitted':[float(v) for v in fit.fittedvalues],'method':f'OLS with Bartlett Newey-West HAC covariance, {lag} annual lags, finite-sample correction and approximate t inference (df={n-2}).','limitations':['Gridded NASA POWER data describe a grid cell, not a city-wide station average.','A linear trend is a summary of this selected period, not a forecast or causal explanation.','HAC uncertainty is approximate with a short annual series; structural breaks and lag choice can affect inference.','Repeatedly selecting periods or variables may increase false-positive findings.','Non-significance does not prove absence of change.']}
