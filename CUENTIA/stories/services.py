#stories/services.py
import logging
from django.conf import settings
from decouple import config
from typing import Dict, Optional, Tuple
import time
from openai import OpenAI

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.api_key = config('OPENAI_API_KEY', default='')
        self.client = None

        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("Cliente OpenAI inicializado correctamente")
            except Exception as e:
                logger.error(f"Error inicializando cliente OpenAI: {str(e)}")
        else:
            logger.warning("OPENAI_API_KEY no configurada - usando modo fallback")

    def generar_cuento_completo(self, datos_formulario: Dict) -> Tuple[str, str, str, str, str]:
        """
        Genera un cuento completo con título, contenido, moraleja e imagen
        """
        try:
            logger.info(f"Iniciando generacion de cuento para: {datos_formulario.get('personaje_principal', 'N/A')}")

            if not self.client:
                logger.info("Cliente OpenAI no disponible, usando fallback")
                return self._generar_cuento_fallback(datos_formulario)

            # 1. Intentar generar el cuento con IA
            logger.info("Intentando generar texto del cuento con IA...")
            try:
                titulo, contenido, moraleja = self._generar_texto_cuento(datos_formulario)
                logger.info("Texto del cuento generado con IA exitosamente")
            except Exception as e:
                logger.warning(f"Error con IA, usando fallback para texto: {str(e)}")
                titulo, contenido, moraleja = self._generar_cuento_fallback(datos_formulario)[:3]

            # 2. Intentar generar la imagen
            logger.info("Intentando generar imagen del cuento...")
            try:
                imagen_url, imagen_prompt = self._generar_imagen_cuento(titulo, contenido, datos_formulario['tema'])
                logger.info("Imagen generada exitosamente")
            except Exception as e:
                logger.warning(f"Error generando imagen, usando placeholder: {str(e)}")
                imagen_url = "/static/images/cuento-placeholder.png"
                imagen_prompt = "Imagen placeholder para el cuento"

            logger.info(f"Cuento generado exitosamente: {titulo}")
            return titulo, contenido, moraleja, imagen_url, imagen_prompt

        except Exception as e:
            logger.error(f"Error generando cuento completo: {str(e)}")
            # Fallback con contenido de ejemplo
            return self._generar_cuento_fallback(datos_formulario)

    def _generar_texto_cuento(self, datos: Dict) -> Tuple[str, str, str]:
        """Genera el texto del cuento usando GPT"""
        if not self.client:
            raise Exception("Cliente OpenAI no disponible")

        prompt = self._construir_prompt_cuento(datos)

        logger.info("Enviando prompt a OpenAI...")

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """Eres un escritor experto en cuentos infantiles mágicos. 
                    Creas historias cautivadoras, educativas y apropiadas para la edad especificada. 
                    Siempre incluyes una moraleja clara y valiosa al final.
                    Tu estilo es descriptivo, imaginativo y lleno de magia."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1500,
            temperature=0.8,
            presence_penalty=0.1,
            frequency_penalty=0.1
        )

        contenido_completo = response.choices[0].message.content.strip()
        logger.info(f"Respuesta recibida de OpenAI: {len(contenido_completo)} caracteres")

        # Procesar la respuesta para extraer título, contenido y moraleja
        titulo, contenido, moraleja = self._procesar_respuesta_cuento(contenido_completo, datos)

        return titulo, contenido, moraleja

    def _generar_imagen_cuento(self, titulo: str, contenido: str, tema: str) -> Tuple[str, str]:
        """Genera una imagen para el cuento usando DALL-E"""
        if not self.client:
            raise Exception("Cliente OpenAI no disponible")

        prompt_imagen = self._construir_prompt_imagen(titulo, contenido, tema)

        logger.info("Generando imagen con DALL-E...")

        response = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt_imagen,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        imagen_url = response.data[0].url

        logger.info("Imagen generada exitosamente")
        return imagen_url, prompt_imagen

    def _construir_prompt_cuento(self, datos: Dict) -> str:
        """Construye el prompt optimizado para generar el cuento"""

        edad_descripcion = {
            '3-5': 'niños de 3 a 5 años (preescolar) - usa vocabulario muy simple, frases cortas y conceptos básicos',
            '6-8': 'niños de 6 a 8 años (primaria temprana) - vocabulario intermedio, puede incluir aventuras simples',
            '9-12': 'niños de 9 a 12 años (primaria tardía) - vocabulario más avanzado, tramas más complejas'
        }.get(datos.get('edad', '6-8'), 'niños de 6 a 8 años')

        longitud_descripcion = {
            'corto': 'un cuento corto de 3-4 párrafos (2-3 minutos de lectura)',
            'medio': 'un cuento de longitud media de 6-8 párrafos (5-7 minutos de lectura)',
            'largo': 'un cuento largo de 10-12 párrafos (10-15 minutos de lectura)'
        }.get(datos.get('longitud', 'medio'), 'un cuento de longitud media')

        tema_elementos = {
            'aventura': 'viajes emocionantes, descubrimientos, valentía, exploración',
            'fantasia': 'magia, criaturas mágicas, mundos encantados, hechizos',
            'amistad': 'compañerismo, lealtad, ayuda mutua, trabajo en equipo',
            'familia': 'amor familiar, tradiciones, apoyo, unión',
            'naturaleza': 'animales, bosques, océanos, cuidado del medio ambiente',
            'ciencia': 'inventos, experimentos, tecnología futurista, descubrimientos',
            'animales': 'mascotas, animales salvajes, comunicación con animales'
        }.get(datos.get('tema', 'aventura'), 'aventuras emocionantes')

        titulo_sugerido = datos.get('titulo', '').strip()
        personaje = datos.get('personaje_principal', 'un niño aventurero')

        prompt = f"""
Escribe {longitud_descripcion} para {edad_descripcion} con las siguientes características:

PERSONAJE PRINCIPAL: {personaje}
TEMA: {datos.get('tema', 'aventura')} - incluye elementos de {tema_elementos}
TÍTULO SUGERIDO: {titulo_sugerido if titulo_sugerido else 'Genera un título creativo y mágico'}

INSTRUCCIONES ESPECÍFICAS:
1. El cuento debe ser completamente apropiado para la edad especificada
2. Usa un lenguaje descriptivo pero accesible para la edad
3. Incluye elementos mágicos y fantásticos que capturen la imaginación
4. La historia debe tener un inicio, desarrollo y final satisfactorio
5. Incluye diálogos naturales para hacer la historia más dinámica
6. Describe escenarios de manera vívida para que el niño pueda imaginarlos
7. El protagonista debe enfrentar un desafío y crecer como personaje
8. Incluye emociones positivas y momentos de emoción
9. Al final, incluye una moraleja clara y valiosa para la vida

FORMATO DE RESPUESTA REQUERIDO:
TÍTULO: [Título creativo y atractivo del cuento]

CUENTO:
[Contenido del cuento dividido en párrafos bien estructurados, con descripciones ricas y diálogos naturales]

MORALEJA:
[Una moraleja clara, positiva y educativa que se derive naturalmente de la historia]

IMPORTANTE: Asegúrate de que la historia sea emocionante, educativa, mágica y completamente apropiada para niños.
"""
        return prompt

    def _construir_prompt_imagen(self, titulo: str, contenido: str, tema: str) -> str:
        """Construye el prompt para generar la imagen del cuento"""

        # Extraer elementos clave del contenido para la imagen
        tema_visual = {
            'aventura': 'adventure scene with maps, treasure, mountains, brave characters',
            'fantasia': 'magical fantasy scene with sparkles, enchanted forest, magical creatures',
            'amistad': 'heartwarming friendship scene with characters helping each other',
            'familia': 'warm family scene with love and togetherness',
            'naturaleza': 'beautiful nature scene with animals, trees, rivers, natural beauty',
            'ciencia': 'futuristic science scene with inventions, space, technology',
            'animales': 'adorable animals in their natural habitat, friendly and cute'
        }.get(tema, 'magical adventure scene')

        prompt_imagen = f"""
Create a beautiful, magical children's book illustration for the story "{titulo}".

Scene description: {tema_visual}

Art style requirements:
- Digital art, vibrant and warm colors
- Whimsical and magical atmosphere
- Child-friendly and enchanting
- Storybook illustration style
- High quality, detailed artwork
- Soft lighting with magical glow
- Suitable for children aged 3-12
- No scary or dark elements
- Include sparkles, soft shadows, and dreamy atmosphere

The image should capture the wonder and magic of childhood stories, with beautiful colors that would appeal to children and create a sense of adventure and imagination.
"""

        return prompt_imagen

    def _procesar_respuesta_cuento(self, respuesta: str, datos_formulario: Dict) -> Tuple[str, str, str]:
        """Procesa la respuesta de OpenAI y extrae título, contenido y moraleja"""

        # Valores por defecto
        titulo_default = datos_formulario.get('titulo', '').strip() or 'El Cuento Mágico'
        contenido_default = respuesta
        moraleja_default = "La bondad y la valentía siempre son recompensadas."

        try:
            # Buscar patrones en la respuesta
            lineas = respuesta.split('\n')
            titulo_extraido = titulo_default
            contenido_extraido = ""
            moraleja_extraida = moraleja_default

            seccion_actual = "contenido"

            for linea in lineas:
                linea = linea.strip()
                if not linea:
                    continue

                if linea.upper().startswith('TÍTULO:'):
                    titulo_extraido = linea.replace('TÍTULO:', '').replace('TITULO:', '').strip()
                    seccion_actual = "titulo"
                elif linea.upper().startswith('CUENTO:'):
                    seccion_actual = "contenido"
                elif linea.upper().startswith('MORALEJA:'):
                    seccion_actual = "moraleja"
                elif seccion_actual == "contenido" and not linea.upper().startswith(
                        ('TÍTULO:', 'TITULO:', 'MORALEJA:')):
                    contenido_extraido += linea + "\n\n"
                elif seccion_actual == "moraleja":
                    moraleja_extraida += linea + " "

            # Limpiar contenido
            contenido_extraido = contenido_extraido.strip()
            moraleja_extraida = moraleja_extraida.strip()

            # Si no se pudo extraer contenido, usar toda la respuesta
            if not contenido_extraido:
                contenido_extraido = respuesta

            logger.info(f"Cuento procesado - Titulo: {titulo_extraido[:50]}...")
            return titulo_extraido, contenido_extraido, moraleja_extraida

        except Exception as e:
            logger.error(f"Error procesando respuesta: {str(e)}")
            return titulo_default, contenido_default, moraleja_default

    def _generar_cuento_fallback(self, datos: Dict) -> Tuple[str, str, str, str, str]:
        """Genera un cuento de fallback mejorado si falla la API"""
        personaje = datos.get('personaje_principal', 'un niño aventurero')
        tema = datos.get('tema', 'aventura')
        edad = datos.get('edad', '6-8')

        # Títulos personalizados por tema
        titulos_por_tema = {
            'aventura': f"La Gran Aventura de {personaje}",
            'fantasia': f"El Mundo Mágico de {personaje}",
            'amistad': f"{personaje} y el Poder de la Amistad",
            'familia': f"La Familia Especial de {personaje}",
            'naturaleza': f"{personaje} y los Secretos del Bosque",
            'ciencia': f"Las Increíbles Invenciones de {personaje}",
            'animales': f"{personaje} y sus Amigos Animales"
        }

        titulo = titulos_por_tema.get(tema, f"La Aventura Mágica de {personaje}")

        # Contenidos personalizados por tema
        contenidos_por_tema = {
            'aventura': f"""
Había una vez {personaje} que vivía en un pequeño pueblo rodeado de montañas misteriosas. Un día, mientras exploraba el bosque cercano, encontró un mapa antiguo que mostraba el camino hacia un tesoro perdido.

Con valentía en el corazón, {personaje} emprendió una emocionante aventura. Cruzó ríos cristalinos, escaló colinas empinadas y resolvió acertijos antiguos. En cada paso del camino, aprendió algo nuevo sobre sí mismo.

Durante su viaje, {personaje} se encontró con otros aventureros que necesitaban ayuda. Sin dudarlo, compartió su comida y les enseñó el camino seguro. Juntos, enfrentaron los desafíos con coraje y determinación.

Al final, {personaje} descubrió que el verdadero tesoro no era oro ni joyas, sino las amistades que había hecho y las lecciones que había aprendido. Regresó a casa siendo más sabio y valiente que nunca.
""",
            'fantasia': f"""
En un reino mágico muy lejano, vivía {personaje} en una casa encantada donde los libros hablaban y las flores cantaban. Un día, una estrella fugaz cayó en su jardín, trayendo consigo una misión especial.

{personaje} descubrió que tenía poderes mágicos únicos que podía usar para ayudar a otros. Con su varita brillante y su corazón puro, emprendió un viaje por tierras encantadas llenas de criaturas fantásticas.

En su camino, {personaje} conoció a un dragón amigable que había perdido su fuego, a un unicornio triste que no podía volar, y a un hada que había olvidado cómo hacer magia. Con paciencia y bondad, ayudó a cada uno a recuperar sus dones especiales.

Al final de su aventura mágica, {personaje} aprendió que la verdadera magia viene del amor y la generosidad. El reino entero celebró su valentía, y desde entonces, la magia floreció más fuerte que nunca.
""",
            'amistad': f"""
{personaje} era nuevo en la escuela y se sentía muy solo. Durante el recreo, se sentaba bajo un gran árbol y observaba a los otros niños jugar, deseando tener amigos con quienes compartir.

Un día, {personaje} vio a otro niño que también estaba solo, leyendo un libro en un rincón. Con valentía, se acercó y le preguntó sobre su historia. Así comenzó una hermosa amistad que cambiaría sus vidas.

Juntos, {personaje} y su nuevo amigo descubrieron que tenían muchas cosas en común. Les gustaban los mismos juegos, las mismas historias, y ambos soñaban con grandes aventuras. Pronto, otros niños se unieron a su grupo.

{personaje} aprendió que hacer amigos requiere ser amable, compartir y estar dispuesto a escuchar. Su círculo de amigos creció, y la escuela se convirtió en un lugar lleno de risas, juegos y momentos especiales que atesoraría para siempre.
"""
        }

        contenido = contenidos_por_tema.get(tema, contenidos_por_tema['aventura'])

        # Moralejas por tema
        moralejas_por_tema = {
            'aventura': "Las aventuras más grandes comienzan cuando tenemos el valor de dar el primer paso y ayudar a otros en el camino.",
            'fantasia': "La verdadera magia está en usar nuestros dones para hacer el bien y ayudar a quienes nos rodean.",
            'amistad': "La amistad verdadera se construye con bondad, comprensión y la disposición de compartir nuestro corazón.",
            'familia': "El amor familiar es el tesoro más grande que podemos tener en la vida.",
            'naturaleza': "Cuidar la naturaleza es cuidar nuestro hogar y el futuro de todos los seres vivos.",
            'ciencia': "La curiosidad y el deseo de aprender nos llevan a descubrir cosas maravillosas.",
            'animales': "Todos los seres vivos merecen amor, respeto y cuidado."
        }

        moraleja = moralejas_por_tema.get(tema, moralejas_por_tema['aventura'])
        imagen_url = "/static/images/cuento-placeholder.png"
        imagen_prompt = f"Imagen placeholder para cuento de {tema}"

        logger.info(f"Cuento fallback generado: {titulo}")
        return titulo, contenido, moraleja, imagen_url, imagen_prompt


# Instancia global del servicio
openai_service = OpenAIService()