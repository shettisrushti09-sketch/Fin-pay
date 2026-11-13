
import { useState, useEffect } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

export default function App() {
  const [token, setToken] = useState(
    () => localStorage.getItem("token") || ""
  );

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [wallet, setWallet] = useState(null);
  const [history, setHistory] = useState([]);
  const [topupAmount, setTopupAmount] = useState("");
  const [paymentAmount, setPaymentAmount] = useState("");
  const [merchant, setMerchant] = useState("1");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [dashboardLoading, setDashboardLoading] = useState(false);

  // Common API function
  async function request(path, method = "GET", body = null, authToken = token) {
    const response = await fetch(API + path, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(authToken
          ? { Authorization: `Bearer ${authToken}` }
          : {})
      },
      ...(body ? { body: JSON.stringify(body) } : {})
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Request failed");
    }

    return data;
  }

  // Load wallet and history
  async function loadDashboard(currentToken = token) {
    if (!currentToken) return;

    setDashboardLoading(true);

    try {
      const [walletData, historyData] = await Promise.all([
        request("/wallet/me", "GET", null, currentToken),
        request("/payments/history", "GET", null, currentToken)
      ]);

      setWallet(walletData);
      setHistory(historyData);
      setMessage("");
    } catch (error) {
      setMessage(error.message);

      if (
        error.message.toLowerCase().includes("token") ||
        error.message.toLowerCase().includes("credentials")
      ) {
        localStorage.removeItem("token");
        setToken("");
        setWallet(null);
        setHistory([]);
      }
    } finally {
      setDashboardLoading(false);
    }
  }

  // Automatically load dashboard after login or page refresh
  useEffect(() => {
    if (token) {
      loadDashboard(token);
    }
  }, [token]);

  // Login
  async function login(e) {
    e.preventDefault();

    try {
      setLoading(true);
      setMessage("");

      const data = await request(
        "/students/login",
        "POST",
        {
          email,
          password
        },
        ""
      );

      if (!data.access_token) {
        throw new Error("Login token not received");
      }

      localStorage.setItem("token", data.access_token);
      setToken(data.access_token);
      setPassword("");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  // Add money
  async function topUp() {
    try {
      const value = Math.round(Number(topupAmount) * 100);

      if (!value || value <= 0) {
        throw new Error("Enter a valid top-up amount");
      }

      await request("/wallet/top-up", "POST", {
        amount_paise: value,
        idempotency_key: "topup-" + crypto.randomUUID()
      });

      setTopupAmount("");
      setMessage("Money added successfully!");

      await loadDashboard();
    } catch (error) {
      setMessage(error.message);
    }
  }

  // Make payment
  async function pay() {
    try {
      const value = Math.round(Number(paymentAmount) * 100);

      if (!value || value <= 0) {
        throw new Error("Enter a valid payment amount");
      }

      const result = await request("/payments/pay", "POST", {
        merchant_id: Number(merchant),
        amount_paise: value,
        idempotency_key: "payment-" + crypto.randomUUID()
      });

      setPaymentAmount("");

      setMessage(
        `Payment successful! Cashback: ₹${(
          result.cashback_paise / 100
        ).toFixed(2)}`
      );

      await loadDashboard();
    } catch (error) {
      setMessage(error.message);
    }
  }

  // Logout
  function logout() {
    localStorage.removeItem("token");

    setToken("");
    setWallet(null);
    setHistory([]);
    setMessage("Logged out successfully");
    setPassword("");
  }

  // Login page
  if (!token) {
    return (
      <div className="login-page">
        <form className="login-card" onSubmit={login}>
          <div className="logo">F</div>

          <h1>Welcome to FinPay</h1>
          <p>Your digital wallet, made simple.</p>

          <label>Email address</label>
          <input
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <label>Password</label>
          <input
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <button type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Login"}
          </button>

          {message && <div className="message">{message}</div>}
        </form>
      </div>
    );
  }

  // Dashboard
  return (
    <div className="app">

      <aside className="sidebar">
        <h2><span>F</span> FinPay</h2>

        <p className="nav-active">▦ &nbsp; Dashboard</p>
        <p>◉ &nbsp; My Wallet</p>
        <p>↗ &nbsp; Payments</p>
        <p>★ &nbsp; Cashback</p>
        <p>▤ &nbsp; Transactions</p>

        <button className="logout" onClick={logout}>
          Logout
        </button>
      </aside>

      <main className="content">

        <header>
          <div>
            <h1>Dashboard</h1>
            <p>Welcome back to your FinPay account.</p>
          </div>

          <div className="profile">Student Account</div>
        </header>

        {message && (
          <div className="notice">{message}</div>
        )}

        {/* Wallet balance */}
        <section className="balance-card">
          <div>
            <p>Available Wallet Balance</p>

            <h1>
              {dashboardLoading && !wallet
                ? "Loading..."
                : wallet
                ? `₹${Number(wallet.balance_rupees).toFixed(2)}`
                : "Unable to load"}
            </h1>

            <span>
              {wallet
                ? `${wallet.tier} Tier`
                : "Wallet information"}
            </span>
          </div>

          <div className="wallet-icon">₹</div>
        </section>

        {/* Actions */}
        <section className="actions">

          <div className="panel">
            <h3>Add Money</h3>
            <p>Add funds to your digital wallet.</p>

            <input
              type="number"
              min="1"
              placeholder="Amount in ₹"
              value={topupAmount}
              onChange={(e) => setTopupAmount(e.target.value)}
            />

            <button onClick={topUp}>
              Add Money
            </button>
          </div>

          <div className="panel">
            <h3>Make a Payment</h3>
            <p>Select a merchant and enter amount.</p>

            <select
              value={merchant}
              onChange={(e) => setMerchant(e.target.value)}
            >
              <option value="1">College Canteen</option>
              <option value="3">College Bookstore</option>
              <option value="4">College Stationery Shop</option>
            </select>

            <input
              type="number"
              min="1"
              placeholder="Amount in ₹"
              value={paymentAmount}
              onChange={(e) => setPaymentAmount(e.target.value)}
            />

            <button onClick={pay}>
              Pay Now
            </button>
          </div>

        </section>

        {/* Transactions */}
        <section className="panel transactions">

          <div className="table-heading">
            <h3>Recent Transactions</h3>

            <button
              className="refresh"
              onClick={() => loadDashboard()}
            >
              Refresh
            </button>
          </div>

          {dashboardLoading && history.length === 0 ? (
            <p>Loading transactions...</p>
          ) : history.length === 0 ? (
            <p>No transactions found.</p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Merchant</th>
                    <th>Amount</th>
                    <th>Cashback</th>
                    <th>Status</th>
                  </tr>
                </thead>

                <tbody>
                  {history.map((item) => (
                    <tr key={item.transaction_id}>
                      <td>{item.merchant_name}</td>
                      <td>₹{Number(item.amount_rupees).toFixed(2)}</td>
                      <td>₹{Number(item.cashback_rupees).toFixed(2)}</td>
                      <td>
                        <span className="success">
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

        </section>

        <button
          className="refresh"
          onClick={() => loadDashboard()}
        >
          Load / Refresh Dashboard
        </button>

      </main>
    </div>
  );
}
