# Application of Linear Algebra Learnings: Haar Wavelets and Image Compression

[![Launch Dashboard](https://img.shields.io/badge/App-Launch_Dashboard_📊-FF4B4B?style=flat&logo=rocket)](https://xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.streamlit.app/)
[![Read Case Study](https://img.shields.io/badge/Research-Full_Case_Study_📚-blue?style=flat&logo=read-the-docs&logoColor=white)](https://jordanchongja.github.io/projects/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/)

![Simulation Dashboard in Action](images/streamlit-dashboard-mainmetrics.gif)

## 💡 The Origin
So in trying to learn more about Machine Learning models, I figured that I would have to learn more about Linear Algebra, and what better source to learn this from than the 3Blue1Brown series on Linear Algebra. Having finished that YouTube series and learnt more about the visualisation of how Linear Transformations work, I decided to put it into practice by redoing a school project that I did during exchange in Lund, on the Discrete Haar Wavelet Transform and try to put the intuition into practice for a simple Image Compression exercise.


## 🧮 Under the Hood
To model the market maker's behavior, the engine handles a few key implementations:
* **The Reservation Price:** Using a CARA (Constant Absolute Risk Aversion) utility framework, the algorithm calculates the subjective valuation of the asset based on current inventory ($q$).
* **Optimal Spread Calibration:** Using the Hamilton-Jacobi-Bellman (HJB) equation to solve for the optimal, asymmetric distance to place bid ($\delta_b$) and ask ($\delta_a$) quotes.
* **Monte Carlo Order Flow:** Simulating the arrival of market orders using a Poisson process to test how the spreads hold up under realistic market microstructure conditions.

## 📊 Key Findings

![distribution PnL Comparison Chart](images/streamlit-dashboard-distributionPandL.png)
![cumulative PnL Comparison Chart](images/streamlit-dashboard-cumulPandL.png)
![Table metrics](images/streamlit-dashboard-tablemetrics.png)

By running the simulation, we can clearly observe how the Avellaneda-Stoikov (AS) inventory-aware strategy solves the fatal flaw of naive market making.

### 1. Superior Risk-Adjusted Returns (Sharpe Ratio)
The naive symmetric strategy typically yields a slightly higher mean return because, by staying anchored to the mid-price, it receives a higher volume of incoming orders.

However, this comes at a massive cost to risk. The AS inventory strategy yields P&L profiles and final inventories that have significantly less variance than the benchmark strategy.

By actively managing inventory, the inventory-aware agent generates a drastically superior Sharpe Ratio, proving that the AS model yields a much more efficient use of capital regardless of the parameter tuning.

### 2. Elimination of Tail Risk
The histogram visually confirms the paper's core conclusion: the AS strategy yields P&L profiles with much smaller variance.

The red AS distribution consistently remains tall and tightly clustered, indicating highly predictable profits.

The blue symmetric distribution spreads wide and flat. Because the symmetric dealer ignores their accumulated stock, they fall victim to "inventory random walks," exposing themselves to severe drawdowns if the market trends against their bloated position.

### 3. A Smoother Equity Curve
Looking at a single path simulation, the symmetric strategy (dotted blue line) is a bumpy ride, highly sensitive to directional market shocks.

The AS strategy (solid red line) demonstrates the power of the subjective "indifference price." By skewing quotes to automatically incentivize trades that flatten their inventory, the dealer locks in a steady, reliable upward equity curve with minimal drawdowns.


## 🎛️ Parameter Sensitivity Analysis

Real-world order books are dynamic, and a successful market-making algorithm cannot rely on static inputs. I built the **Sensitivity Analysis** module because a dealer's sensitivity to inventory changes directly dictates their quoting aggressiveness. This section allows users to explore the non-linear relationship between market chaos and algorithm configuration.

![Sensitivity Analysis](images/streamlit-dashboard-sensitivityanalysis.gif)


### The 1D Gamma Sweep (Risk Aversion)
![1D Parameter Sweep](images/streamlit-dashboard-sensitivityanalysis-1D.png)
* The Sharpe ratio does not simply scale infinitely with higher risk aversion. As $\gamma$ increases from near-zero (where the strategy behaves identically to the naive benchmark), the Sharpe ratio climbs and hits an optimal "sweet spot." However, if $\gamma$ gets too high, the dealer becomes overly defensive. They widen their spreads to extreme lengths to avoid holding inventory, which severely chokes off trade execution and degrades overall profitability. 

### The 2D Heatmap (The "Goldilocks" Zone)
![2D Heatmap](images/streamlit-dashboard-sensitivityanalysis-2D.png)
* Mapping Volatility ($\sigma$) against Risk Aversion ($\gamma$) reveals a complex performance surface. Unsurprisingly, rising market volatility compresses the Sharpe ratio across the board. The visual proves that static parameters fail in dynamic markets; to maintain peak capital efficiency, a quantitative strategist must continuously re-calibrate their risk aversion to adapt to prevailing market volatility.


## 💻 Tech Stack
* **Language:** Python 3.10
* **Math/Simulation:** `numpy`, `scipy`
* **Visualization/Frontend:** `streamlit`, `matplotlib`

## 🚀 Run the Simulation Locally

1. Clone the repository:
   ```bash
   git clone [https://github.com/jordanchongja/avellaneda-stoikov-MM-single-limit-order.git](https://github.com/jordanchongja/avellaneda-stoikov-MM-single-limit-order.git)
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Boot up the Streamlit interface:
   ```bash
   streamlit run app.py
   ```

## 📖 Deep Dive & Documentation
For the full mathematical derivation, the Hamilton-Jacobi-Bellman setup, and the comparative performance metrics, please visit the full research notebook on my website:

👉 **[Read the full breakdown at jordanchongja.github.io](https://jordanchongja.github.io/notes/posts/Paper%20-%20High-frequency%20trading%20in%20a%20limit%20order%20book/)**