# Factor Modelling with Fama-French-Macbeth Model 

## --- Repo: Work in Progress ---
I started on this project quite early on, and I thought that I could use the fundamental data extracted from WRDS to build a kind of "Factor Zoo" from all the different factors. I theorized that at least one of the factors had to be profitable, right? My initial approach was to train a model based on a PCA of the key factors that had the most impact. 

But I quickly realized that doing this was basically Overfitting 101. I put a pause on this experiment to look for more rigorous models and alternative sources of true alpha, rather than just mining for spurious correlations.

### The Fama-French Model
The Fama-French model, either the classic 3-factor or the updated 5-factor model, defines the specific economic risk factors that drive asset returns. These models expand upon the Capital Asset Pricing Model (CAPM). CAPM starts with the thesis that a stock's excess returns can be explained purely as a coefficient (beta) upon the market's excess return, plus some error rate. 

The formula for CAPM is expressed as:

$$
R_{i,t} - R_{f,t} = \alpha_i + \beta_M (R_{M,t} - R_{f,t}) + \epsilon_{i,t}
$$

*(Where $R_i$ is the asset return, $R_f$ is the risk-free rate, $R_M$ is the market return, and $\beta_M$ is the asset's sensitivity to the market).*

The Fama-French Model builds upon this concept by arguing that market risk alone is insufficient. It adds additional fundamental factors to capture a broader spectrum of systematic risk: specifically, **Size (SMB)** and **Value (HML)** for the three-factor model:

$$
R_{i,t} - R_{f,t} = \alpha_i + \beta_1 (R_{M,t} - R_{f,t}) + \beta_2 SMB_t + \beta_3 HML_t + \epsilon_{i,t}
$$

And later incorporating **Profitability (RMW)** and **Investment (CMA)** to create the five-factor model:

$$
R_{i,t} - R_{f,t} = \alpha_i + \beta_1 (R_{M,t} - R_{f,t}) + \beta_2 SMB_t + \beta_3 HML_t + \beta_4 RMW_t + \beta_5 CMA_t + \epsilon_{i,t}
$$

### The Fama-MacBeth Regression: Taming the Factor Zoo
If compiling fundamental data leads to a chaotic "Factor Zoo," Fama-MacBeth is the rigorous statistical filter required to make sense of it. It is a two-step regression procedure designed specifically to test asset pricing models and estimate the actual risk premium ($\lambda$) investors receive for bearing those risks. 

Crucially, it is designed to mitigate the statistical problem of cross-sectional correlation in asset returns, which standard panel regressions fail to handle, providing a much-needed defense against overfitting.

*   **Step 1 (Time-Series Regression):** First, we regress individual asset or portfolio returns against our proposed factors to estimate the factor loadings ($\hat{\beta}$) for each asset. For $K$ factors:
    
$$
R_{i,t} - R_{f,t} = \alpha_i + \sum_{j=1}^K \beta_{i,j} F_{j,t} + \epsilon_{i,t}
$$

*   **Step 2 (Cross-Sectional Regression):** Next, for *every single time period* (e.g., every month $t$), we run a cross-sectional regression of all asset returns against their previously estimated $\hat{\beta}$s from Step 1. This generates a time series of risk premia coefficients ($\hat{\gamma}$) for each factor:
    
$$
R_{i,t} - R_{f,t} = \gamma_{0,t} + \sum_{j=1}^K \gamma_{j,t} \hat{\beta}_{i,j} + \eta_{i,t}
$$

*   **The Purpose (Averaging):** Finally, we take the time-series average of these cross-sectional coefficients to find the true risk premium ($\lambda$):
    
$$
\hat{\lambda}_j = \frac{1}{T} \sum_{t=1}^T \hat{\gamma}_{j,t}
$$

**In summary:** While a naive PCA might grab any combination of factors that happened to look profitable in the past, a quantitative strategist uses the **Fama-MacBeth methodology** to robustly test whether the theoretical risk factors proposed by models like **Fama-French** are actually, consistently priced into the market over time. It is the definitive test to separate true alpha from statistical noise.