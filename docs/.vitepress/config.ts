import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Unihra SDK',
  description: 'Official Python SDK for Unihra SEO Content Analysis API',
  lang: 'en-US',
  base: '/unihra_sdk/',
  cleanUrls: true,

  head: [
    ['meta', { name: 'theme-color', content: '#646cff' }],
    ['meta', { name: 'og:type', content: 'website' }],
    ['meta', { name: 'og:site_name', content: 'Unihra SDK Docs' }],
  ],

  themeConfig: {
    siteTitle: 'Unihra SDK',

    nav: [
      { text: 'Guide', link: '/guide/getting-started', activeMatch: '/guide/' },
      { text: 'Reference', link: '/reference/client', activeMatch: '/reference/' },
      { text: 'Changelog', link: '/changelog' },
      {
        text: 'v1.7.0',
        items: [
          { text: 'PyPI', link: 'https://pypi.org/project/unihra/' },
          { text: 'GitHub', link: 'https://github.com/Unihra/unihra_sdk' },
        ],
      },
      { text: 'REST API →', link: 'https://unihra.ru/docs' },
    ],

    sidebar: {
      '/guide/': [
        {
          text: 'Getting Started',
          items: [
            { text: 'Introduction', link: '/guide/getting-started' },
            { text: 'Installation', link: '/guide/installation' },
            { text: 'Authentication', link: '/guide/authentication' },
          ],
        },
        {
          text: 'Core Features',
          items: [
            { text: 'Running Analysis', link: '/guide/analysis' },
            { text: 'Result Sections', link: '/guide/result-sections' },
            { text: 'Streaming', link: '/guide/streaming' },
            { text: 'Saving & Export', link: '/guide/export' },
            { text: 'Sharing Analyses', link: '/guide/sharing' },
          ],
        },
        {
          text: 'Integrations',
          items: [
            { text: 'CLI', link: '/guide/cli' },
            { text: 'MCP Server', link: '/guide/mcp' },
          ],
        },
      ],
      '/reference/': [
        {
          text: 'Python API',
          items: [
            { text: 'UnihraClient', link: '/reference/client' },
            { text: 'Exceptions', link: '/reference/exceptions' },
          ],
        },
        {
          text: 'Tools',
          items: [
            { text: 'CLI Flags', link: '/reference/cli' },
            { text: 'MCP Tools', link: '/reference/mcp' },
          ],
        },
      ],
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/Unihra/unihra_sdk' },
    ],

    search: {
      provider: 'local',
    },

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2026–present Unihra',
    },

    editLink: {
      pattern: 'https://github.com/Unihra/unihra_sdk/edit/main/docs/:path',
      text: 'Edit this page on GitHub',
    },

    lastUpdated: {
      text: 'Updated at',
      formatOptions: { dateStyle: 'medium' },
    },
  },
})
