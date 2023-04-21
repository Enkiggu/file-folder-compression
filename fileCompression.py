import os
from PIL import Image
import argparse
import struct
import zlib
import zipfile

#IMAGE COMPRESSOR
def get_size_format(image_size, factor=1024, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if image_size < factor:
            return f"{image_size:.2f}{unit}{suffix}"
        image_size /= factor
    return f"{image_size:.2f}Y{suffix}"
def compress_given_img(image_name, new_size_ratio=0.9, quality=90, image_width=None, height_width=None, to_jpg=True):
    img = Image.open(image_name)
    print("[*] Fotoğrafının boyutu: ", img.size)
    image_size = os.path.getsize(image_name)
    print("[*] Sıkıştırılmadan önceki boyut: ", get_size_format(image_size))
    if new_size_ratio < 1.0:
        img = img.resize((int(img.size[0] * new_size_ratio), int(img.size[1] * new_size_ratio)), Image.ANTIALIAS)
        print("Yeni fotoğraf boyutu: ", img.size)
    elif image_width and height_width:
        img = img.resize((image_width, height_width), Image.ANTIALIAS)
        print("Yeni fotoğraf boyutu: ", img.size)
    filename, ext = os.path.splitext(image_name)
    if to_jpg:
        new_filename = f"{filename}_compressed.jpg"
    else:
        new_filename = f"{filename}_compressed{ext}"
    try:
        img.save(new_filename, quality=quality, optimize=True)
    except OSError:
        img = img.convert("RGB")
        img.save(new_filename, quality=quality, optimize=True)
    print("Kaydedilmiş dosya ismi: ", new_filename)
    new_image_size = os.path.getsize(new_filename)
    print("Sıkıştırıldıktan sonra boyutu: ", get_size_format(new_image_size))
    saving_diff = new_image_size - image_size
    print(f"Orijinal fotoğrafın boyut değişme yüzdesi: {saving_diff / image_size * 100:.2f}%")

#FILE COMPRESSOR
#Extension, signature
EXTENSION,SIGNATURE = '.enk',b'\x7fEN'
def compress_file(input_file_path, output_file_path):
    index = output_file_path.index(".")
    file_name = output_file_path[:index]
    with open(input_file_path, mode='rb') as input_file:
        data = input_file.read()

    compressed_data = zlib.compress(data)

    header = struct.pack('3s', SIGNATURE)
    compressed_size = struct.pack('I', len(compressed_data))
    uncompressed_size = struct.pack('I', len(data))

    with open(file_name + "_compressed" + EXTENSION, mode='wb') as output_file:
        output_file.write(header)
        output_file.write(compressed_size)
        output_file.write(uncompressed_size)
        output_file.write(compressed_data)

    return file_name + "_compressed" + EXTENSION
def decompress_file(input_file_path, output_file_path):
    index = output_file_path.index(".")
    ext = output_file_path[index:]
    with open(input_file_path, mode='rb') as input_file:
        if input_file.read(3) != SIGNATURE:
            raise ValueError("Geçersiz dosya formatı.")

        compressed_size = struct.unpack('I', input_file.read(4))[0]
        uncompressed_size = struct.unpack('I', input_file.read(4))[0]

        compressed_data = input_file.read(compressed_size)

        data = zlib.decompress(compressed_data)

    if input_file_path.endswith('.enk'):
        output_file_path = os.path.splitext(output_file_path)[0] + str(ext)

    with open(output_file_path, mode='w') as output_file:
        output_file.write(data.decode('utf-8'))


#FOLDER COMPRESSOR
def compress_folder(source_folder, output_filename):
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                zip_file.write(os.path.join(root, file))
def decompress_folder(source_file, output_folder):
    with zipfile.ZipFile(source_file, 'r') as zip_file:
        zip_file.extractall(output_folder)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dosya sıkıştırmak için kişisel python scripti")
    parser.add_argument("-i","--image", help="Verilen resim sıkıştırılacak ve/veya boyutlandırılacaktır.")
    parser.add_argument("-f","--file", help="Verilen dosyayı sıkıştırılacak ve/veya boyutlandırılacaktır.(.enk dosyasına çevirir)")
    parser.add_argument("-dc","--decompress", help="Verilen dosyayı çözmek için kullanın.(.enk dosyası olmalıdır)")
    parser.add_argument("-o","--output", help="Çıktı dosyasının adını belirtir.(Uzantıyı belirtin)")
    parser.add_argument("-j", "--to-jpg", action="store_true",
                        help="Görüntünün JPEG formatına dönüştürülüp dönüştürülmeyeceğini belirtir.")
    parser.add_argument("-q", "--quality", type=int,
                        help="Kalite seviyesi 0'dan (en kötü) 95'e (en iyi) kadar değişen bir tamsayıdır. Varsayılan 90'dır.",
                        default=90)
    parser.add_argument("-r", "--resize-ratio", type=float,
                        help="0 ila 1 arasındaki boyut oranını yeniden boyutlandırır, 0.5 olarak ayarlamak, görüntünün genişliğini ve yüksekliğini 0.5 ile çarpar. Varsayılan 1.0.",
                        default=1.0)
    parser.add_argument("-w", "--width", type=int,
                        help="Görüntünün yeni genişliği, `height` parametresiyle ayarlanmış olduğuna emin olun")
    parser.add_argument("-ht", "--height", type=int,
                        help="Görüntünün yeni yüksekliği, `width` parametresiyle ayarlanmış olduğuna emin olun")
    args = parser.parse_args()
    if args.image:
        print("=" * 50)
        print("Fotoğraf ismi:", args.image)
        print("JPEG'e dönüştürme:", args.to_jpg)
        print("Kalite:", args.quality)
        print("Yeniden boyutlandırma oranı:", args.resize_ratio)
        if args.width and args.height:
            print("Genişlik:", args.width)
            print("Yükseklik:", args.height)
        print("=" * 50)
        compress_given_img(args.image, args.resize_ratio, args.quality, args.width, args.height, args.to_jpg)

    if args.file and args.decompress:
        print("Aynı anda sıkıştırma ve çözme işlemi yapılamaz.")
    elif args.file  and "." in args.file:
        file_name = compress_file(args.file, args.file)
        print("=" * 50)
        print("Dosya ismi:", args.file)
        print("Çıktı dosyası ismi:", file_name)
        print("=" * 50)
    elif args.file:
        compress_folder(args.file, args.file + ".enk")
    elif args.decompress and args.output and "." in args.output:
        decompress_file(args.decompress, args.output)
        print("=" * 50)
        print("Dosya ismi:", args.decompress)
        print("Çıktı dosyası ismi:", args.output)
        print("=" * 50)
    elif args.decompress and not args.output:
        print("Lütfen -o/--output parametresi ile çıktı dosyasının ismini belirtin.(Uzantıyı varsa belirtin)")
    elif args.decompress and args.output:
        decompress_folder(args.decompress, args.output)
    elif args.decompress and not args.output or not args.decompress and args.output:
        print("Çözme işlemi için çıktı dosyası ismi belirtmelisiniz.")