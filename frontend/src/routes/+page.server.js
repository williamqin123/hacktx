export function load({ cookies }) {
	return {
		isAuthenticated: Boolean(cookies.get('auth_token'))
	};
}
