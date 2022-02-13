import asyncio
from datetime import datetime
import io
import torch
import torch.nn as nn
import torch.optim as optim

from PIL import Image
from torchvision import transforms, models
from torchvision.models.vgg import model_urls
from models.nst import Normalization, ContentLoss, StyleLoss, VGG_NST

IMG_MAX_SIZE = 512

# desired depth layers to compute style/content losses :
CONTENT_LAYERS_DEFAULT = ['conv_4']
STYLE_LAYERS_DEFAULT = ['conv_1', 'conv_2', 'conv_3', 'conv_4', 'conv_5']

# remove pixel when odd
def resize_by_pix(img):
    width, height = img.size
    width = width-1 if width%2 == 1 else width
    height = height-1 if height%2 == 1 else height
    img = img.crop((0, 0, width, height))
    return img, width, height

# Size up by mirroring (style to content size)
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

# Size down by cutting (style to content size)
def size_down(img, dif, mode):
  half_dif = dif//2
  width, height = img.size
  if mode == 'W':
    rez_img = img.crop((half_dif, 0, width - half_dif, height))
  elif mode == 'H':
    rez_img = img.crop((0, half_dif , width, height - half_dif))

  return rez_img

def prep_imgs(content_img, style_img):
  
    content_img, ci_width, ci_height = resize_by_pix(content_img)
    style_img, si_width, si_height = resize_by_pix(style_img)

    if ci_width > si_width:
        style_img = size_up(style_img, ci_width-si_width, 'W')
    elif ci_width < si_width:
        style_img = size_down(style_img, si_width - ci_width, 'W')

    if ci_height > si_height:
        style_img = size_up(style_img, ci_height-si_height, 'H')
    elif ci_height < si_height:
        style_img = size_down(style_img, si_height-ci_height, 'H')

    loader_list = [transforms.ToTensor()]
    if ci_height > IMG_MAX_SIZE or ci_width > IMG_MAX_SIZE:
        loader_list.insert(0, transforms.Resize(IMG_MAX_SIZE))
    
    loader = transforms.Compose(loader_list)

    # fake batch dimension required to fit network's input dimensions
    content_img = loader(content_img).unsqueeze(0)
    style_img = loader(style_img).unsqueeze(0)

    return content_img, style_img


def get_style_model_and_losses(cnn, style_img, content_img,
                               content_layers=CONTENT_LAYERS_DEFAULT,
                               style_layers=STYLE_LAYERS_DEFAULT):
    # normalization module
    normalization = Normalization(torch.tensor([0.485, 0.456, 0.406]), torch.tensor([0.229, 0.224, 0.225]))

    # just in order to have an iterable access to or list of content/syle
    # losses
    content_losses = []
    style_losses = []

    # assuming that cnn is a nn.Sequential, so we make a new nn.Sequential
    # to put in modules that are supposed to be activated sequentially
    model = nn.Sequential(normalization)
    i = 0  # increment every time we see a conv
    for layer in cnn.children():
        if isinstance(layer, nn.Conv2d):
            i += 1
            name = 'conv_{}'.format(i)
        elif isinstance(layer, nn.ReLU):
            name = 'relu_{}'.format(i)
            # The in-place version doesn't play very nicely with the ContentLoss
            # and StyleLoss we insert below. So we replace with out-of-place
            # ones here.
            layer = nn.ReLU(inplace=False)
        elif isinstance(layer, nn.MaxPool2d):
            name = 'pool_{}'.format(i)
        elif isinstance(layer, nn.BatchNorm2d):
            name = 'bn_{}'.format(i)
        else:
            raise RuntimeError('Unrecognized layer: {}'.format(layer.__class__.__name__))

        model.add_module(name, layer)

        if name in content_layers:
            # add content loss:
            target = model(content_img).detach()
            content_loss = ContentLoss(target)
            model.add_module("content_loss_{}".format(i), content_loss)
            content_losses.append(content_loss)

        if name in style_layers:
            # add style loss:
            target_feature = model(style_img).detach()
            style_loss = StyleLoss(target_feature)
            model.add_module("style_loss_{}".format(i), style_loss)
            style_losses.append(style_loss)

    # now we trim off the layers after the last content and style losses
    for i in range(len(model) - 1, -1, -1):
        if isinstance(model[i], ContentLoss) or isinstance(model[i], StyleLoss):
            break

    model = model[:(i + 1)]
    return model, style_losses, content_losses

def get_input_optimizer(input_img):
    # this line to show that input is a parameter that requires a gradient
    optimizer = optim.LBFGS([input_img])
    return optimizer

async def run_style_transfer(cnn, content_img, style_img, input_img, num_steps=400,
                       style_weight=1000000, content_weight=1):
    """Run the style transfer."""
    print('Building the style transfer model..')
    model, style_losses, content_losses = get_style_model_and_losses(cnn, style_img, content_img)

    # We want to optimize the input and not the model parameters so we
    # update all the requires_grad fields accordingly
    input_img.requires_grad_(True)
    model.requires_grad_(False)

    optimizer = get_input_optimizer(input_img)

    print('Optimizing..')

    loop = asyncio.get_event_loop()
    run = [0]
    while run[0] <= num_steps:

        def closure():
            # correct the values of updated input image
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
            if run[0] % 50 == 0:
                print("run {}:".format(run))
                print('Style Loss : {:4f} Content Loss: {:4f}'.format(
                    style_score.item(), content_score.item()))
                print()

            return style_score + content_score

        # optimizer.step(closure)
        await loop.run_in_executor(None ,optimizer.step, closure)

    # a last correction...
    with torch.no_grad():
        input_img.clamp_(0, 1)

    return input_img

async def neural_style_transfer (content_img, style_img):
    start_time = datetime.now()
    content_img, style_img = prep_imgs(content_img, style_img)
    input_img = content_img.clone()

    model_urls['vgg19'] = model_urls['vgg19'].replace('https://', 'http://')
    cnn = models.vgg19(pretrained=True).features[:29].eval()

    result = await run_style_transfer(cnn, content_img, style_img, input_img, num_steps = 200)
    buf = io.BytesIO()
    trans1 = transforms.ToPILImage()
    result = trans1(result[0])
    result.save(buf, format='JPEG')
    result = buf.getvalue()
    print(datetime.now() - start_time)
    return result


async def neural_style_transfer2 (content_img, style_img):
    start_time = datetime.now()
    content_img, style_img = prep_imgs(content_img, style_img)
    input_img = content_img.clone()

    cnn = VGG_NST.eval()

    result = await run_style_transfer(cnn, content_img, style_img, input_img, num_steps = 200)
    buf = io.BytesIO()
    trans1 = transforms.ToPILImage()
    result = trans1(result[0])
    result.save(buf, format='JPEG')
    result = buf.getvalue()
    print(datetime.now() - start_time)
    return result