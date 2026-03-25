/** @type {import('tailwindcss').Config} */
module.exports = {
	darkMode: ['class'],
	content: [
		'./pages/**/*.{ts,tsx}',
		'./components/**/*.{ts,tsx}',
		'./app/**/*.{ts,tsx}',
		'./src/**/*.{ts,tsx}',
	],
	theme: {
		container: {
			center: true,
			padding: '2rem',
			screens: {
				'2xl': '1400px',
			},
		},
		extend: {
			// Dribbble-inspired color palette for K3s Sentinel
			colors: {
				// Core colors from Dribbble design
				surface: '#030303',        // Dark background
				surfaceLight: '#0a0a0a', // Slightly lighter surface
				border: '#1a1a1a',         // Subtle borders
				borderLight: '#2a2a2a',    // Lighter borders

				// Accent colors
				accent: {
					green: '#8EC060',       // Primary green accent
					greenDark: '#435E2A',   // Darker green
					orange: '#F95106',      // Orange highlight
					blue: '#0F3DDE',        // Blue for interactive
					white: '#FAFAFA',       // Off-white text
				},

				// Semantic colors
				border: 'hsl(var(--border))',
				input: 'hsl(var(--input))',
				ring: 'hsl(var(--ring))',
				background: '#030303',
				foreground: '#FAFAFA',

				primary: {
					DEFAULT: '#8EC060',    // Green accent
					light: '#A8D080',
					dark: '#6BA040',
					foreground: '#030303',
				},
				secondary: {
					DEFAULT: '#0F3DDE',    // Blue interactive
					light: '#2D5AEF',
					dark: '#0A2DB8',
					foreground: '#FAFAFA',
				},
				accent: {
					DEFAULT: '#F95106',    // Orange highlight
					light: '#FF6A30',
					dark: '#D94500',
					foreground: '#FAFAFA',
				},
				destructive: {
					DEFAULT: '#EF4444',
					foreground: '#FAFAFA',
				},
				muted: {
					DEFAULT: '#1a1a1a',
					foreground: '#8a8a8a',
				},
				popover: {
					DEFAULT: '#0a0a0a',
					foreground: '#FAFAFA',
				},
				card: {
					DEFAULT: '#0a0a0a',
					foreground: '#FAFAFA',
				},
				// Status colors
				success: '#8EC060',
				warning: '#F95106',
				info: '#0F3DDE',
				error: '#EF4444',
			},
			borderRadius: {
				lg: 'var(--radius)',
				md: 'calc(var(--radius) - 2px)',
				sm: 'calc(var(--radius) - 4px)',
			},
			keyframes: {
				'accordion-down': {
					from: { height: 0 },
					to: { height: 'var(--radix-accordion-content-height)' },
				},
				'accordion-up': {
					from: { height: 'var(--radix-accordion-content-height)' },
					to: { height: 0 },
				},
				'glow': {
					'0%, 100%': { opacity: 0.5 },
					'50%': { opacity: 1 },
				},
			},
			animation: {
				'accordion-down': 'accordion-down 0.2s ease-out',
				'accordion-up': 'accordion-up 0.2s ease-out',
				'glow': 'glow 2s ease-in-out infinite',
			},
			backgroundImage: {
				'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
				'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
			},
		},
	},
	plugins: [require('tailwindcss-animate')],
}
