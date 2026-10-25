<script lang="ts">
	import type { PageProps } from './$types';
	import { ArrowRight, ChefHat, Heart } from '@lucide/svelte';
	import { Button } from '#lib/components/ui/button';

	let { data }: PageProps = $props();
</script>

<svelte:head>
	<title>Prandium AI — Meals made your way</title>
	<meta
		name="description"
		content="Good food, planned around you."
	/>
</svelte:head>

<main class="landing-page">
	<div class="landing-shell">
		<header class="landing-header">
			<a href="/" class="brand" aria-label="Prandium AI home">
				<span class="brand-mark"><ChefHat class="size-5" /></span>
				<span>Prandium <span class="brand-accent">AI</span></span>
			</a>
		</header>

		<section class="hero" aria-labelledby="welcome-heading">
			<div class="hero-copy">
				<p class="eyebrow"><Heart class="size-4" /> MADE WITH YOU IN MIND</p>
				<h1 id="welcome-heading">Good food, <span>your way.</span></h1>
				<p class="hero-description">Meals you love, made simple.</p>
			</div>

			<div class="welcome-actions">
				<div class="hero-actions">
					<Button
						href={data.isAuthenticated ? '/logged-in-app/studio' : '/setup'}
						size="lg"
						class="get-started-button"
					>
						Get started
						<ArrowRight class="ml-2 size-4" />
					</Button>
					<Button href="/login" variant="outline" size="lg" class="login-button">
						Login
					</Button>
				</div>
			</div>
		</section>

		<footer class="landing-footer">
			<span>Prandium AI</span>
			<span>Made for your kind of day.</span>
		</footer>
	</div>
</main>

<style>
	.landing-page {
		position: relative;
		display: flex;
		min-height: 100svh;
		overflow: auto;
		align-items: center;
		justify-content: center;
		background:
			radial-gradient(ellipse at 50% 18%, color-mix(in oklab, var(--primary) 9%, transparent), transparent 38rem),
			var(--background);
	}

	.landing-shell {
		position: relative;
		z-index: 1;
		width: min(100% - 2rem, 900px);
		margin: 0 auto;
	}

	.landing-header {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 1.5rem 0;
		animation: landing-enter 500ms ease-out both;
	}

	.brand {
		display: inline-flex;
		align-items: center;
		gap: 0.65rem;
		color: var(--foreground);
		font-size: 1.1rem;
		font-weight: 700;
		letter-spacing: -0.04em;
		text-decoration: none;
	}

	.brand-mark {
		display: grid;
		width: 2.25rem;
		height: 2.25rem;
		place-items: center;
		border-radius: 0.75rem;
		background: var(--primary);
		color: var(--primary-foreground);
	}

	.brand-accent {
		color: var(--primary);
	}

	.hero {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1.75rem;
		padding: clamp(2rem, 5vh, 3.5rem) 0;
	}

	.hero-copy {
		width: 100%;
		text-align: center;
		animation: landing-enter 650ms 80ms ease-out both;
	}

	.eyebrow {
		display: inline-flex;
		align-items: center;
		gap: 0.55rem;
		color: var(--primary);
		font-size: 0.75rem;
		font-weight: 700;
		letter-spacing: 0.14em;
		text-align: center;
	}

	h1 {
		margin-top: 0.8rem;
		font-family: var(--font-heading);
		font-size: clamp(3rem, 8vw, 5.4rem);
		font-weight: 700;
		letter-spacing: -0.075em;
		line-height: 1.02;
	}

	h1 span {
		color: var(--primary);
	}

	.hero-description {
		margin-top: 0.8rem;
		color: var(--muted-foreground);
		font-size: clamp(1rem, 1.6vw, 1.2rem);
	}

	.hero-actions {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		justify-content: center;
		gap: 1rem;
	}

	.welcome-actions {
		animation: landing-enter 650ms 240ms ease-out both;
	}

	:global(.get-started-button) {
		min-height: 3rem;
		padding-inline: 1.25rem;
		box-shadow: 0 8px 24px color-mix(in oklab, var(--primary) 23%, transparent);
	}

	.landing-footer {
		display: flex;
		justify-content: center;
		gap: 1rem;
		border-top: 1px solid color-mix(in oklab, var(--border) 70%, transparent);
		padding: 1.25rem 0;
		color: var(--muted-foreground);
		font-size: 0.75rem;
	}

	.landing-footer span:first-child {
		color: var(--foreground);
		font-weight: 650;
	}

	@keyframes landing-enter {
		from {
			opacity: 0;
			transform: translateY(12px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	@media (max-width: 850px) {
		.landing-shell {
			width: min(100% - 2rem, 760px);
		}
	}

	@media (max-width: 520px) {
		.landing-shell {
			width: min(100% - 2rem, 1160px);
		}

		.hero {
			gap: 1.35rem;
			padding: 2rem 0;
		}

		h1 {
			font-size: clamp(3rem, 14vw, 4.2rem);
		}

		.hero-description {
			font-size: 0.96rem;
		}

		.hero-actions {
			gap: 0.75rem;
		}

		.landing-footer span:last-child {
			text-align: center;
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.landing-header,
		.hero-copy,
		.welcome-actions {
			animation: none;
		}
	}
</style>
