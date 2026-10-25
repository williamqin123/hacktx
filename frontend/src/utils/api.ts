const PUBLIC_API_URL = "https://prandium-ai.vercel.app";

export async function apiFetch(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  const requestUrl = input instanceof Request ? input.url : input.toString();
  const url = new URL(requestUrl, `${PUBLIC_API_URL}/`);
  const response = await fetch(url, {
    ...init,
    credentials: "include",
  });

  if (response.status === 401) {
    window.location.assign(`${PUBLIC_API_URL}/logout`);
    throw new Error("Unauthorized");
  }

  return response;
}
