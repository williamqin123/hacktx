const PUBLIC_API_URL = "https://prandium-ai.vercel.app";

export async function apiFetch(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  const response = await fetch(PUBLIC_API_URL + "/" + input, {
    ...init,
    credentials: "include",
  });

  if (response.status === 401) {
    window.location.assign(`${PUBLIC_API_URL}/logout`);
    throw new Error("Unauthorized");
  }

  return response;
}
