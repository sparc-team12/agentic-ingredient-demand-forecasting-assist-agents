// `/login` route (ACRI-66).
import { LoginForm } from "@/components/auth/login-form";

export default function LoginRoute() {
  return (
    <main className="centered-page">
      <div className="card card--narrow">
        <h1>Log in</h1>
        <LoginForm />
      </div>
    </main>
  );
}
