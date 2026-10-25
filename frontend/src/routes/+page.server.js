import { redirect } from '@sveltejs/kit';

export function load({ cookies }) {
	if (cookies.get('auth_token')) {
		throw redirect(302, '/logged-in-app/studio');
	}
}
