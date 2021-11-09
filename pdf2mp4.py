import sys, fitz, tqdm, os, subprocess, threading, sys, random
from fitz.fitz import Pixmap # import the bindings

def popen_and_call(on_exit, on_exit_args, popen_args):
    """
    Runs the given args in a subprocess.Popen, and then calls the function
    on_exit when the subprocess completes.
    on_exit is a callable object, and popen_args is a list/tuple of args that 
    would give to subprocess.Popen.
    """
    def run_in_thread(on_exit, on_exit_args, popen_args):
        proc = subprocess.Popen(popen_args)
        proc.wait()
        on_exit(on_exit_args)
        return
    thread = threading.Thread(target=run_in_thread, args=(on_exit, on_exit_args, popen_args))
    thread.start()
    # returns immediately after the thread starts
    return thread


def remove_intermediate_folder(folder):
    os.system(f"rm -r {folder}")
    print(f'Intermediate subfolder {folder} is removed.')

if len(sys.argv)>1:
    fname = sys.argv[1]  # get filename from command line
else:
    print(f'\t Usage: {sys.argv[0].split("/")[-1]} input.pdf part_size')
    sys.exit("Error, No input file is provided.")


run_id = random.randint(0, 100000)
tmp_folder = f'tmp/tmp_{run_id:05d}'
print(f'Temporary folder: {tmp_folder}')

doc = fitz.open(fname)  # open document

fname_without_extension = "".join(fname.split('.')[:-1]) # remove extension from filename

os.makedirs(f'{tmp_folder}', exist_ok=True)


steps = 3               # page split count
microsteps = 1         # scroll step
between_page_step = 5  # space between pages

part_size = 100          # default number of pages in each part

if len(sys.argv) > 2:
    part_size = int(sys.argv[2])

zoom_x = 2
zoom_y = 2 

offset_x1 = 50
offset_x2 = offset_x1

mat = fitz.Matrix(zoom_x, zoom_y)
output_counter = -1

for page_counter in tqdm.tqdm(range(doc.pageCount)):
    subfolder = f'{page_counter//part_size:03d}'
    os.makedirs(f'{tmp_folder}/{subfolder}', exist_ok=True)

    page = doc[page_counter] 
    rect = page.rect  # the page rectangle
    page_width, page_height = int(rect.width), int(rect.height)

    step_size = page_height // steps

    pix = None
    tag = None

    for i in range(0, page_height, microsteps):
        output_counter += 1
        # output_filename = f"{tmp_folder}/{fname_without_extension}-{page.number:04d}_{i:04d}.png"
        output_filename = f"{tmp_folder}/{subfolder}/{fname_without_extension}-{output_counter:06d}.png"
        if os.path.exists(output_filename) and i>0:
            print(output_filename + " already exists.")
            continue

        if i+step_size < page_height:
            tag = None
            clip = fitz.Rect(0 + offset_x1, i, page_width - offset_x2, i+step_size)  # the area we want
            pix = page.get_pixmap(matrix=mat, clip=clip)
        elif page_counter < doc.pageCount-1:
                

            pixEmpty = Pixmap(pix.colorspace, (0, 0, pix.width, pix.height), False)
            pixEmpty.set_rect((0,0,pixEmpty.width, pixEmpty.height), [0,0,0])
            pix = None

            clip = fitz.Rect(0 + offset_x1, i, page_width - offset_x2, min(page_height, i+step_size))  # the area we want
            pix1 = page.get_pixmap(matrix=mat, clip=clip)
            # pix1.save(f"{tmp_folder}/{fname_without_extension}-{page.number+1:04d}_{i:04d}_1.png")  # store image as a PNG

            if tag==None:
                tag = 1
                page2 = doc[page_counter + 1]
            clip2 = fitz.Rect(0 + offset_x1, 0, page_width - offset_x2, i + step_size - page_height)  # the area we want
            pix2 = page2.get_pixmap(matrix=mat, clip=clip2)
            # pix2.save(f"{tmp_folder}/{fname_without_extension}-{page.number+1:04d}_{i:04d}_2.png")  # store image as a PNG

            pix1.set_origin(0, 0)
            pix2.set_origin(0, 0)
            pixEmpty.set_origin(0, 0)

            pixEmpty.copy(pix1, (0, 0, pix1.width, pix1.height))
            
            pixEmpty.set_origin(0, -pix1.height-between_page_step)
            pixEmpty.copy(pix2, (0, 0, pix2.width, pix2.height))
            pixEmpty.set_origin(0, 0)

            pix = pixEmpty


        pix.save(output_filename)  # store image as a PNG

    # run ffmpeg
    if (page_counter % part_size) == part_size-1 or page_counter == doc.pageCount-1:
        # cmd_str = f'ffmpeg -y -r 3 -i {tmp_folder}/{subfolder}/{fname_without_extension}-%06d.png -c:v libx264 -r 3 {fname_without_extension}_{page_counter//part_size}.mp4'
        # cmd_str = f'ffmpeg -y -r 24 -i {tmp_folder}/{subfolder}/{fname_without_extension}-%06d.png -vf crop=ceil(iw/2)*2:ceil(ih/2)*2,scale=-1:1080 -vcodec libx264 -crf 18 -pix_fmt yuv420p -r 24 {fname_without_extension}_{page_counter//part_size}.mp4'
        cmd_str = f'ffmpeg -y -r 24 -i {tmp_folder}/{subfolder}/{fname_without_extension}-%06d.png -vf scale=1440:900 -vcodec libx264 -crf 0 -pix_fmt yuv420p -r 24 {fname_without_extension}_{page_counter//part_size}.mp4'
        cmd_lst = cmd_str.split(' ')
        print(cmd_lst)
        # subprocess.Popen(cmd_lst, close_fds=True)
        popen_and_call(remove_intermediate_folder, f'{tmp_folder}/{subfolder}', cmd_lst)
        output_counter = -1

print(f'Please remove "{tmp_folder}" folder after all outputs are generated.')

 

