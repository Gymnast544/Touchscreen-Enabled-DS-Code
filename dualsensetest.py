import pygame
import time
pygame.init()


buttons = {0:"Y", 1:"B", 2:"A", 3:"X"}

controllers=[]
for i in range(pygame.joystick.get_count()):
    joystick = pygame.joystick.Joystick(i)
    joystick.init()
    if joystick.get_name()=="Wireless Controller" and joystick.get_numaxes()==6 and joystick.get_numbuttons()==14 and joystick.get_numhats()==1:
        print("Valid controller")
    controllers.append(joystick)

print("Press cross on the desired joystick")

running = True
while running:
    for event in pygame.event.get():
        if event.type==pygame.JOYBUTTONDOWN:
            print(event.button)
            if event.button == 1:
                joystick = event.joy
                for controller in controllers:
                    if controller.get_id()!=joystick:
                        controller.quit()
                        #de-inits all irrelevant controllers
                running = False
        if event.type == pygame.JOYHATMOTION:
            print(event.value)

