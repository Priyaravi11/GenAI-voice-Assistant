import { FormEvent, useState } from "react";
import { loginCustomer } from "../../services/api";
import type { AuthSession } from "../../types";

type LoginProps = {
  onLogin: (session: AuthSession) => void;
};

function Login({ onLogin }: LoginProps) {
  const [custId, setCustId] = useState("C274");
  const [accountId, setAccountId] = useState("A001");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const session = await loginCustomer({
        cust_id: custId,
        account_id: accountId,
      });
      onLogin(session);
    } catch {
      setError("Invalid login details. Check the customer ID and account ID.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="login-screen">
      <section className="login-panel">
        <div className="login-brand">
          <span>VA</span>
          <div>
            <strong>VoiceAI</strong>
            <small>Customer session login</small>
          </div>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div>
            <p className="eyebrow">Verified Access</p>
            <h1>Start a customer support session</h1>
          </div>

          <label>
            Customer ID
            <input
              value={custId}
              onChange={(event) => setCustId(event.target.value)}
              placeholder="C274"
              autoComplete="username"
              required
            />
          </label>

          <label>
            Account ID
            <input
              value={accountId}
              onChange={(event) => setAccountId(event.target.value)}
              placeholder="A001"
              required
            />
          </label>

          {error ? <p className="login-error">{error}</p> : null}

          <button className="primary-button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}

export default Login;
