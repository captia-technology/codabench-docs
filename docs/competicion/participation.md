---
title: "Participation"
description: "Fijar los términos que acepta el participante al registrarse y decidir si los registros se aprueban solos o uno a uno."
sidebar_position: 2
---

# Participation

**Objetivo:** fijar los términos que acepta el participante al registrarse y decidir si los registros se aprueban solos o uno a uno.

## Ajustes de la pestaña

Pestaña **Participation**:

- **Terms**: términos y condiciones de la competición (texto/markdown). Se muestran en un modal antes de registrarse y también quedan disponibles como pestaña "Terms" dentro de la competición pública.
- **Auto approve registration requests**: si está marcado, cualquiera que se registre entra automáticamente; si no, la competición muestra "This competition requires approval from the competition organizers" y un organizador o un colaborador debe aprobar cada registro manualmente (**Resources → Participants**) antes de que el participante pueda enviar submissions.
- **Allow robot submissions**: si se deja sin marcar, las cuentas de tipo robot —las que envían por API en vez de por la interfaz— también pasan por aprobación manual. Se puede cambiar después.
- **Whitelist Emails**: restringe el registro a una lista de correos o dominios. Es la vía para una competición interna sin abrirla a cualquiera con cuenta en la plataforma.

## Grupos de participantes

Debajo de los ajustes anteriores se pueden definir **grupos**, cada uno con su **Group name**, una **Queue (optional)** propia y sus miembros. Sirven para encaminar las submissions de unos participantes a una cola distinta de la del resto —por ejemplo, reservar los recursos con GPU a un subconjunto—.

Es una función reciente: el encaminamiento por grupos llegó en **Codabench v1.28** y se afinó en la v1.30. Si la instancia que se usa es anterior, esta sección no aparece.

**Siguiente paso:** [Pages](./pages.md) — el contenido informativo que verán los participantes.
