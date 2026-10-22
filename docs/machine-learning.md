# Machine learning

The model predicts the probability that the next trading period closes higher. Feature engineering includes returns, SMA/EMA trend, RSI/MACD/momentum, ATR/volatility/range, volume ratios, and distances from trend and 52-week extrema.

Training uses a chronological 80/20 split and three-window expanding time-series validation. Logistic Regression, Random Forest, Gradient Boosting, and XGBoost share the same frozen feature matrix. The registry stores version, algorithm, window, feature list, parameters, evaluation metrics, artifact location, and activation state. Probability thresholds become BUY/HOLD/SELL strategy inputs; predictions never reach a broker directly.
