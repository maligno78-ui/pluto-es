# Pluto TV España - M3U

Lista M3U de canales Pluto TV España. Se actualiza automáticamente 2 veces al día (12:00 y 00:00 hora española).

## URL del M3U

```
https://raw.githubusercontent.com/maligno78-ui/pluto-es/main/pluto_es.m3u
```

Añade esta URL a tu reproductor IPTV.

## Cómo funciona

- Un script Python consulta la API oficial de Pluto TV
- Obtiene todos los canales disponibles en España (~143)
- Genera un archivo M3U con URLs directas y EPG
- GitHub Actions lo ejecuta cada 12 horas automáticamente

