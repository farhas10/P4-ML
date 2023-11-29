from camera import CameraHandler


def main():
  camera = CameraHandler()
  while True:
    cmd = input("Want to take another image? (y/n)\n: ")
    if cmd == 'y':
      camera.get_processed_image(save=True)
    elif cmd == 'n':
      break


if __name__ == '__main__':
  main()
