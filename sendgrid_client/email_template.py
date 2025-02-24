template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Notificação de Contrato</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }
            .container {
                max-width: 600px;
                margin: 20px auto;
                background: #ffffff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }
            .header {
                font-size: 18px;
                font-weight: bold;
                text-align: justify;
            }
            .content {
                margin: 20px 0;
                font-size: 16px;
                text-align: justify;
            }
            .button-container {
                text-align: center;
                margin-top: 10px;
            }
            .button {
                display: inline-block;
                background: #007BFF;
                color: #ffffff;
                padding: 10px 15px;
                text-decoration: none;
                border-radius: 5px;
                font-size: 16px;
            }
            .footer {
                margin-top: 20px;
                font-size: 12px;
                color: #666;
                text-align: center;
                background-color: #f0f0f0;
                padding: 15px;
                border-radius: 0 0 8px 8px;
            }
            .footer img {
                max-width: 40%;
                height: auto;
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            "$content$"
            <div class="footer">
                <img src="https://storage.googleapis.com/sitts-project-media-bucket/logos/banner-colored.png" alt="Banner">
                <p>Este é um e-mail automático. Por favor, não responda.</p>
                <p>2025, todos os direitos reservados.</p>
            </div>
        </div>
    </body>
    </html>
"""

# <p class="header">Olá $username$,</p>
# <p class="content">Um novo contrato foi cadastrado para você. Confira os detalhes clicando no botão abaixo:</p>
# <div class="button-container">
#     <a href="#" class="button">Ver Contrato</a>
# </div>
# <p class="footer">Este é um e-mail automático. Por favor, não responda.</p>
