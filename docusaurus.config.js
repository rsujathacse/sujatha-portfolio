// @ts-check
// See: https://docusaurus.io/docs/api/docusaurus-config

import {themes as prismThemes} from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Sujatha R',
  tagline:
    '10+ years translating complex cloud and AI systems into clear, developer-ready docs.',
  favicon: 'img/favicon.ico',


  future: {
    v4: true,
  },

  url: 'https://rsujathacse.github.io',
  baseUrl: '/',
  organizationName: 'rsujathacse',
  projectName: 'rsujathacse.github.io',

  onBrokenLinks: 'throw',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  // Disable default preset docs/blog because we are using multiple docs plugins
  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: false,
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  // Separate doc sections (each tab is independent)
  plugins: [
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'docs',
        path: 'docs/docs',
        routeBasePath: 'docs',
        sidebarPath: './sidebarsDocs.js',
      },
    ],
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'apis',
        path: 'docs/apis',
        routeBasePath: 'apis',
        sidebarPath: './sidebarsApis.js',
      },
    ],
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'architecture',
        path: 'docs/architecture',
        routeBasePath: 'architecture',
        sidebarPath: './sidebarsArchitecture.js',
      },
    ],
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'aiml',
        path: 'docs/aiml',
        routeBasePath: 'aiml',
        sidebarPath: './sidebarsAiml.js',
      },
    ],
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'strategy',
        path: 'docs/strategy',
        routeBasePath: 'strategy',
        sidebarPath: './sidebarsStrategy.js',
      },
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      colorMode: {
        respectPrefersColorScheme: true,
      },

      navbar: {
        title: 'Sujatha R',
        logo: {
          alt: 'Sujatha R',
          src: 'img/logo.svg',
        },
        items: [
          {to: '/aiml/intro', label: 'AI/ML Docs', position: 'left'},
          {to: '/docs/intro', label: 'Docs', position: 'left'},
          {to: '/apis/intro', label: 'APIs', position: 'left'},
          {to: '/architecture/intro', label: 'Architecture', position: 'left'},
          {to: '/strategy/intro', label: 'Content Strategy', position: 'left'},
          {to: '/experience', label: 'Experience', position: 'left'},
        
        ],
      },

footer: {
  style: "dark",
  links: [
    {
      items: [
        { label: "LinkedIn", href: "https://www.linkedin.com/in/rsujathatech/" },
        { label: "GitHub", href: "https://github.com/rsujathacse" },
        { label: "Email", href: "mailto:rsujathacse@gmail.com" },
        { label: "My talk(s)", to: "/talks/writing-the-future" },
         { label: `© ${new Date().getFullYear()} Sujatha R`, href: "#" },
      ],
    },
  ],

},




      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
      },
    }),
};

export default config;