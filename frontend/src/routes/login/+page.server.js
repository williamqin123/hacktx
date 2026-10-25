import { redirect } from "@sveltejs/kit";

export function load({ cookies }) {
  const token = cookies.get("auth_token");

  if (token) {
    throw redirect(302, "/logged-in-app/studio");
  }

  throw redirect(302, "https://prandium-ai.vercel.app/login", {
    // hardcoded
    external: true,
  });
}
