/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {}
	},
	plugins: [require('daisyui')],
	daisyui: {
		themes: [
			{
				light: {
					...require("daisyui/src/theming/themes")["light"],
					primary: "#3b82f6",
					secondary: "#8b5cf6",
					accent: "#06b6d4",
					neutral: "#1f2937",
					"base-100": "#ffffff",
				},
				dark: {
					...require("daisyui/src/theming/themes")["dark"],
					primary: "#3b82f6",
					secondary: "#8b5cf6",
					accent: "#06b6d4",
					neutral: "#1f2937",
					"base-100": "#0f172a",
				}
			}
		],
		darkTheme: "dark"
	}
};
