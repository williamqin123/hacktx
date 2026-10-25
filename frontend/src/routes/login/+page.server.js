import { redirect } from "@sveltejs/kit";

export function load({ cookies }) {
  const token = cookies.get("auth_token");

  if (token) {
    throw redirect(302, "/logged-in-app/studio");
  }

  throw redirect(302, "http://localhost:5001/login", { external: true });
}
