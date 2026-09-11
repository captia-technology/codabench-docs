## Qué cambia

<!-- Dos líneas. Qué páginas tocas y por qué. Si corrige un issue: `Cierra #NN`. -->

## Fuente

<!--
De dónde sale lo que afirmas: URL de la documentación oficial de Codabench, u observación directa
de la interfaz (qué pantalla y cuándo). Si el cambio es solo de forma —estilo, enlaces, scripts—,
escribe «sin cambio de contenido» y sigue.
-->

## Antes de pedir revisión

Los tres comandos que corre el CI. Pasarlos aquí evita el ciclo de empujar, esperar y corregir:

```bash
python scripts/check_docs.py          # invariantes de docs/
python scripts/build_nav.py --check   # navegación, mapa de la guía y docs-map al día
npm run build                         # SIN --locale; es el mismo build que publica Vercel
```

- [ ] `python scripts/check_docs.py` en verde
- [ ] `python scripts/build_nav.py --check` en verde — si he añadido, movido o renombrado
      páginas, antes he declarado el documento en `SECCIONES` y he ejecutado
      `python scripts/build_nav.py --apply`
- [ ] `npm run build` termina sin errores
- [ ] Nada publicable que identifique a nadie: ni correos con dominio real, ni IPs, ni
      credenciales, ni URLs de instancias internas de Codabench. El repositorio es privado; **el
      sitio no lo es**

> **Si no aparece la preview de Vercel, mira esto antes de pensar que Vercel se ha roto.**
> `vercel.json` trae un `ignoreCommand` que compara **el último commit** (`HEAD^` contra `HEAD`)
> contra esta lista de rutas vigiladas:
>
> `docs` · `src` · `static` · `docusaurus.config.js` · `sidebars.js` · `package.json` ·
> `package-lock.json` · `vercel.json`
>
> Si el último commit de la tanda no toca ninguna de ellas —un retoque en `scripts/`, en
> `.github/`, en `docs-meta/` o en el `README.md`—, Vercel **no construye y no publica**, aunque
> algún commit anterior del mismo pull request sí tocara `docs/`. Es lo que se quiere: no gastar
> un build en cambios que no alteran el sitio. Cuando sí quieras el despliegue, haz que el último
> commit toque una ruta vigilada o lanza **Redeploy** desde el panel de Vercel.
