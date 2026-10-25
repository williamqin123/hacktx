<script lang="ts">
	import { page } from '$app/state';
	import {
		Sparkles,
		LayoutDashboard,
		BookOpen,
		User,
		Settings,
		Bookmark,
		ShoppingCart
	} from '@lucide/svelte';

	let { children } = $props();

	const tabs = [
		{ label: 'Profile', href: '/logged-in-app/profile', icon: User },
		{ label: 'Studio', href: '/logged-in-app/studio', icon: Sparkles },
		{ label: 'Meal Plans', href: '/logged-in-app/meal-plans', icon: BookOpen },
		{ label: 'Saved Meals', href: '/logged-in-app/saved-meals', icon: Bookmark },
		{ label: 'Cart', href: '/logged-in-app/shopping-cart', icon: ShoppingCart },
		//{ label: 'Orders', href: '/logged-in-app/orders/', icon: LayoutDashboard },
		//{ label: 'Settings', href: '/logged-in-app/settings', icon: Settings }
	];
</script>

<div class="app-layout">
	<main class="content-container">
		{@render children()}
	</main>

	<footer class="navbar">
		<nav class="nav-tabs" aria-label="Main navigation">
			{#each tabs as tab}
				{@const active =
					tab.href === '/'
						? page.url.pathname === '/'
						: page.url.pathname === tab.href ||
							page.url.pathname.startsWith(tab.href + '/')}

				<a
					href={tab.href}
					class:active
					aria-current={active ? 'page' : undefined}
					class="nav-tab"
				>
					<tab.icon size={23} strokeWidth={active ? 2.3 : 1.8} />
					<span>{tab.label}</span>
				</a>
			{/each}
		</nav>
	</footer>
</div>

<style>
	:global(*) {
		box-sizing: border-box;
	}

	.app-layout {
		min-height: 100dvh;
	}

	.content-container {
		min-height: 100dvh;
		padding-bottom: calc(84px + env(safe-area-inset-bottom, 0px));
	}

	.navbar {
		position: fixed;
		z-index: 100;
		right: 0;
		bottom: 0;
		left: 0;
		padding: 8px 8px calc(8px + env(safe-area-inset-bottom, 0px));

		/* Always use dark theme */
		background: rgba(28, 28, 30, 0.96);
		backdrop-filter: blur(24px);
		-webkit-backdrop-filter: blur(24px);
		border-top: 1px solid rgba(255, 255, 255, 0.12);
		color-scheme: dark;
	}

	.nav-tabs {
		display: grid;
		grid-template-columns: repeat(5, minmax(0, 1fr));
		width: 100%;
		max-width: 600px;
		margin: 0 auto;
	}

	.nav-tab {
		display: flex;
		min-width: 0;
		min-height: 54px;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 4px;
		color: #98989f;
		text-decoration: none;
		font-size: 10px;
		font-weight: 500;
		-webkit-tap-highlight-color: transparent;
		transition: color 150ms ease;
	}

	.nav-tab span {
		overflow: hidden;
		max-width: 100%;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.nav-tab.active {
		color: #0a84ff;
		font-weight: 600;
	}

	.nav-tab:focus-visible {
		outline: 2px solid #0a84ff;
		outline-offset: -2px;
		border-radius: 10px;
	}
</style>