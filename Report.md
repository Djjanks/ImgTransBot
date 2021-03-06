# Отчет по проделанной работе

## Введение
В данной работе реализуется Телеграм бот для изменения стиля картинок. 
Тэг Телеграм бота: @ImgTransBot
Проверить асинхронность на боте с HerokuБ маловероятно, так как не хвататет выделенной памяти. Если связаться со мной, могу запустить бот локально с тегом  @SandBox3323Bot. В нем можно будет проверить асинхронность и картинки будут больше размером.
Вы можете легко запустить данного бота у себя локально, для этого необходимо выполнить следующие действия:
1) Скачать репозиторой
2) Создать в папке с проектом bat файл:
```sh
@echo off
call %~dp0venv\Scripts\activate
set BOT_TOKEN= ТОКЕН_ВАШЕГО_ТЕЛЕГРАМ_БОТА
set MODE=LOCAL
python do.py
pause
```
3) Зайти в requirements.txt и выбрать нужные ссылки для pytorch: 6 и 7 строка - win10, 8 и 9 - linux
4) Создать виртуальную среду и произвести установку пакетов из requirements.txt
5) Запустить, созданный ранее bat файл.

К сожалению не смог сдвинуться с тестового примера по машинному обучению и перенести логику в кастомный класс. Возможно получится осуществить это в дальнейшем.
Отчет в репозитории report.md
К сожалению не удалось завершить работу полностью, так как встретил большое количество трудностей по пути.
Основные трудности вызывало отсутствие опыта программирования на Python и реализации проектов.
Основные шаги реализации проекта:
- Телеграмм бот, webhook и деплой на Heroku
- Создание тестовой модели обучения для проверки работы телеграмм бота
- Корректировка модели для асинхронной работы
- Вспомогательные функции
- Проблемы, которые требуют решения

## Телеграмм бот
Первым этапом было короткое изучение фреймворков, позволяющих реализовать бота. Выбор пал на aiogram.
В начале мной был опробован пример с официального сайта aiogram https://docs.aiogram.dev/en/latest/quick_start.html. Реализация локальная.
Следующим шагом стало создание репозитория на github, регистрация и настройка Heroku. Деплой был настроен на commit на master ветке.
Реализация webhook была взята из репозитория https://github.com/aahnik/webhook-aiogram-heroku. Проверка показала, что webhook работает и "будит" бота.

Изначально настрой был оптимистичным, в связи с чем хотелось примерно следующую структуру диалога:
1. /любой_стиль: запускает медленную NST
2. /предобученные_модели: работает на предобученной модели 
2.1. /художник_1
2.2. /художник_...
2.3. /художник_n
3. /обрезка изображений: вы можете подрезать изображение прямо здесь для удобства
3.1. /удалить сверху
3.2. /удалить снизу
3.3. /и т.д.

А это означало, что надо строить сложные диалоги с запоминанием состояния и возможностью писать лог сообщений. 
После анализа разных способов реализации был выбран интересный способ, описанный в статье: https://3-info.ru/post/8953. По сути создается класс (chat_dispatcher), который обеспечивает разделение разных чатов и хранит состояние. При этом хранение состояния происходит в оперативной памяти и нет необходимости добавлять какую-то БД. 
Данная реализация позволяет очень просто строить диалоговую систему бота.

Webhook готов, деплой на Heroku настроен, бот, способный к сложным веткам диалога, реализован. Следующей задачей становится реализация функции изменения картинки.
Тестово сделал простое объединение картинок с таймаутом и запустил бота для проверки асинхронности. time.sleep(60) является синхронной функцией, поэтому бот не отвечал никому. пока был запущен процесс другим пользователем. Однако с asyncio.sleep(60) работала. Значит необходимо производить модификацию функции обучения в дальнейшем.
Изучения принципов работы асинхронности позволило понять, как можно будет сделать асинхронным обучение модели, а именно за счет шагов оптимизатора, между которыми можно будет делать переключение между потоками.
На удивление, одной из проблем стала реализация принятия картинки и ее отправка пользователю без сохранения на диск. С приемом изображения не сразу стало все понятно, как Телеграм их отправляет, будут ли так же приниматься картинки из пересылаемых сообщений (будут). Для отправки картинки обратно пользователю необходимо преобразовать ее в битовое значение.

## Модель

Для начала в качестве реализации машинного обучения был взят пример с сайта PyTorch https://pytorch.org/tutorials/advanced/neural_style_tutorial.html.
Так как из модели требуется только первые 11 словев. Была сохранена модель обрезанная по необходимым слоям, что позволило сократить вес программы.

Установленные цели по модели:
1. Перенести модель в класс
2. Научиться сохранять веса из предобученной сети только по необходимым слоям, чтобы модель занимала меньше места.
3. Найти оптимальные слои модели, обеспечивающие хорошее качество работы и достаточную скорость
4. Рассмотреть другие реализации моделей и опробовать так же их.

К сожалению по данному блоку столкнулся с трудностями на самом первом пункте и не успел углубиться в вопрос.

Были изучены следующие источники:
1. Модель для обучения под конкретные стили https://github.com/zhanghang1989/PyTorch-Multi-Style-Transfer
2. Проект по GAN-ам с большим кол-вом примеров https://github.com/junyanz/pytorch-CycleGAN-and-pix2pix
3. MobilNET для применения предобученных стилей https://github.com/mmalotin/pytorch-fast-neural-style-mobilenetV2
4. Статья https://towardsdatascience.com/implementing-neural-style-transfer-using-pytorch-fd8d43fb7bfa
5. Статья https://www.pluralsight.com/guides/artistic-neural-style-transfer-with-pytorch

## Корректировка моедли для асинхронной работы
Асинхронность была обеспечена с помощью библиотеки asyncio, за счет выделения отдельного потока на цикле оптимизатора. Минусом данного подходя является то, что две запущенных генерации картинки будут работать параллельно, увеличивая время создания для обоих пользователей, а не только для второго.
```sh
    optimizer = get_input_optimizer(input_img)
    loop = asyncio.get_event_loop()
    run = [0]
    while run[0] <= num_steps:
        def closure():
            with torch.no_grad():
                input_img.clamp_(0, 1)
            optimizer.zero_grad()
            model(input_img)
            style_score = 0
            content_score = 0
            for sl in style_losses:
                style_score += sl.loss
            for cl in content_losses:
                content_score += cl.loss
            style_score *= style_weight
            content_score *= content_weight
            loss = style_score + content_score
            loss.backward()
            run[0] += 1
            return style_score + content_score

        await loop.run_in_executor(None ,optimizer.step, closure)
```

## Вспомогательные функции

Для упрощения работы пользователя было решено добавить функции, которые будут изменять размеры картинок, которые отправляет пользователь.
Были написаны следующие функции на базе пакета PIL:
1. Уменьшение картинки на один пиксель, по высоте или ширине, если количество пикселей нечетное
```sh
# remove pixel when odd
def resize_by_pix(img):
    width, height = img.size
    width = width-1 if width%2 == 1 else width
    height = height-1 if height%2 == 1 else height
    img = img.crop((0, 0, width, height))
    return img, width, height
```
Данная функция нужна для упрощения работы остальных функций. Так как по четным количеством пикселей проще работать.
2. Увеличение картинки до необходимой ширины/высоты путем смещения ее в центр и отзеркаливания соответствующих краем на необходимое ко-во пикселей. 
```sh
def size_up(img, dif, mode):
  half_dif = dif//2
  width, height = img.size
  if mode == 'W':
    part1 = img.crop((0, 0, half_dif, height)).transpose(Image.FLIP_LEFT_RIGHT)
    part2 = img.crop((width-half_dif, 0, width, height)).transpose(Image.FLIP_LEFT_RIGHT)
    rez_img = Image.new(img.mode, (width + dif, height))
    rez_img.paste(img, (half_dif, 0))
    rez_img.paste(part1, (0,0))
    rez_img.paste(part2, (width + half_dif,0))

  elif mode == 'H':
    part1 = img.crop((0, 0, width, half_dif)).transpose(Image.FLIP_TOP_BOTTOM)
    part2 = img.crop((0, height-half_dif, width, height)).transpose(Image.FLIP_TOP_BOTTOM)
    rez_img = Image.new(img.mode, (width, height + dif))
    rez_img.paste(img, (0, half_dif))
    rez_img.paste(part1, (0,0))
    rez_img.paste(part2, (0, height+half_dif))

  return rez_img
```
3. Уменьшение картинки путем обрезания
```sh
def size_down(img, dif, mode):
  half_dif = dif//2
  width, height = img.size
  if mode == 'W':
    rez_img = img.crop((half_dif, 0, width - half_dif, height))
  elif mode == 'H':
    rez_img = img.crop((0, half_dif , width, height - half_dif))

  return rez_img
```
В проекте все картинки стиля подгоняются под размер картинок контента, отзеркаливнием (увеличение) или обрезанием (уменьшение), чтобы не терять стиль при его обычном растягивании или сжатии.

## Выводы

Проекты делать интересно, но для погружения в часть с ML необходимо быть хорошо подкованным в остальных аспектах создания проектов.
Буду заниматься дальше.
