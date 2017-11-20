'''
Created on 09/12/2010

@author: thomas
'''
import os #@UnusedImport
import sys
import time #@UnusedImport
import random #@UnusedImport
import string #@UnusedImport
import cPickle as pickle

from behavan.bacocos.gui import * #@UnusedWildImport

if net_options.pyglet_reactor:
    from pygletreactor import pygletreactor
    pygletreactor.install()

# network modules (twisted)
from twisted.internet import reactor, task, defer
from twisted.internet.protocol import _InstanceFactory
from twisted.protocols import amp
from twisted.python import log
import cmd


def bailout(reason):
    ''' close network due to error '''
    reason.printTraceback()
    shutdown()

def shutdown(result=''):
    ''' close network gracefully '''
    if options.use_log:
        my.stout.close()
    reactor.stop()
#    pyglet.app.exit()

def free_director():
    director.window.set_exclusive_keyboard(exclusive=False)

def director_run_no_loop(scene):
    ''' to allow integration of twisted and pyglet'''

    director.scene_stack.append(director.scene)
    director._set_scene(scene)


def twisted_draw():
    ''' to allow integration of twisted and pyglet'''
    while not director.window.has_exit:
        # coiterates with twisted mainloop

        pyglet.clock.tick()
        director.window.dispatch_events()

        director.window.clear()

        if director.next_scene is not None:
            director._set_scene(director.next_scene)

        if not director.scene_stack:
            pyglet.app.exit()

        # draw all the objects
        director.scene.visit()

        # finally show the FPS
        if director.show_FPS:
            director.fps_display.draw()

        director.window.flip()
        yield

class AskReady(MessageLayerStyled):
    is_event_handler = True

    def __init__(self):
        text = my.net_msg['ready']
        super(AskReady, self).__init__(text, back_color=my.layout['color']['back ready'], rich_text=True)

    def on_key_press(self, symbol, modifiers):
        if symbol == key.SPACE:
            c.ready()

class ErrorMessage(MessageLayerStyled):

    def __init__(self, text):
        super(ErrorMessage, self).__init__(text, text_style='error')

class BAClient(CocosController, amp.AMP):

    '''
    Client Controller with a customized Assynchronous Messaging Protocol.
    Holds display data and controls the experiment from server commands.
    '''

    def __init__(self):
        super(BAClient, self).__init__()

    # overloaded cocos methods
    def create_layers(self):
        '''Creates scene layers.'''
        # layers
        lr.back = ColorLayer(*my.layout['color']['back window'])

    def create_client_layers(self):
        ''' use this method to create layers after connection '''
        lr.instruction = MessageLayerStyled('instruction')
        lr.end = MessageEnd()
        lr.gui = GUIBase()

    # overrides CocosController method
    def cocos_app_exit(self):
        shutdown()

    # AMP methods
    def makeConnection(self, transport):
        '''overrides default TCP delay with no delay'''
        if not transport.getTcpNoDelay():
            transport.setTcpNoDelay(True)
        super(BAClient, self).makeConnection(transport)

    # TODO: maybe explore using AMP.connectionLost to display a message!

    # command methods

    @cmd.StopClient.responder
    def stop_client(self):
        pyglet.clock.schedule_once(shutdown, 1)
        return {}

    @cmd.AskReady.responder
    def ask_ready(self):
        director.replace(Scene(AskReady()))
        return {}

    @cmd.AcceptObserver.responder
    def accept_observer(self):
        my.c_id = net_options.observer_id
        director.replace(Scene(MessageLayerStyled('observer connected!')))
        #TODO: add "observer connected" to ba_net_msg.ini
        self.update_observer()
        return {}

    @cmd.ClientLeft.responder
    def client_left(self):
        director.push(Scene(ErrorMessage(my.net_msg['participant left'])))
        free_director()
        return {}

    @cmd.GetConfigRegion.responder
    def get_config_region(self, pickle_cfg):
        my.regioncfg = pickle.loads(pickle_cfg)
        my.CSV_DELIMIT = my.regioncfg['csv delimiter']
        my.DECIMAL_SEPARATOR = my.regioncfg['decimal separator']
        return {}

    @cmd.GetConfigExp.responder
    def get_config_exp(self, pickle_cfg):
        my.expcfg.merge(pickle.loads(pickle_cfg))
        return {}

    @cmd.GetConfigS_msg.responder
    def get_config_s_msg(self, pickle_cfg):
        my.s_msg = pickle.loads(pickle_cfg)
        return {}

    @cmd.GetConfigNet_msg.responder
    def get_config_net_msg(self, pickle_cfg):
        my.net_msg = pickle.loads(pickle_cfg)
        return {}

    @cmd.GetConfigMessage.responder
    def get_config_message(self, pickle_cfg):
        my.message = pickle.loads(pickle_cfg)
        return {}

    @cmd.GetConfigLayout.responder
    def get_config_layout(self, pickle_cfg):
        my.layout = pickle.loads(pickle_cfg)
        return {}

    @cmd.GetConfigGUI.responder
    def get_config_gui(self, pickle_cfg):
        my.guicfg = pickle.loads(pickle_cfg)
        return {}

    @cmd.GetConfigSave.responder
    def get_config_save(self, pickle_cfg):
        if options.use_save:
            my.save.merge(pickle.loads(pickle_cfg))
        return {}

    @cmd.FixConfigs.responder
    def fix_configs(self):
        self.fix_received_configs()
        return {}

    def fix_received_configs(self):
        '''Placeholder for custom fixes to received configs'''
        pass

    @cmd.ObserverLeft.responder
    def observer_left(self):
        return {}

    @cmd.RejectClient.responder
    def reject_client(self):
        director.replace(Scene(ErrorMessage(my.net_msg['rejected connection'])))
        free_director()
        return {}

    @cmd.SetClientID.responder
    def set_client_id(self, client_id):
        my.c_id = client_id
        director.replace(Scene(MessageLayerStyled('connected!')))
        # lets update the client based on configs received and client id
        self.update_client()
        return {}

    @cmd.Start.responder
    def start(self):
        if not net_options.observer:
            show, start = self.check_start()
        else:
            start = True
            show = self.get_start_scene()
        if start:
            # no need to call start_session method -- that is for non-networked experiments
            self.set_session_started()
        director.replace(show)
        # TODO: could be show instruction here
        return {}

    @cmd.EndSession.responder
    def end_session(self, status=''):
        self.unschedule_all()
        self.session_ended = True
        if status == 'concluded':
            lr.end.concluded()
        self.custom_end_session(status)
        director.replace(Scene(lr.back, lr.end))
        return {}

    # methods for scheduling (using dt from pyglet.clock)

    def cant_connect(self, dt, reason):
        print reason
        if len(reason) > 800:
            reason = reason[0:800]
        reason = 'connection error: %s : verify host' % reason
        # TODO: use localized message
        director.replace(Scene(MessageLayerStyled(reason)))
        free_director()

    # event triggered (ex: mouse/key press/release)
    def update_observer(self):
        # overload this one for your usecase
        self.update_client()
        lr.gui.is_event_handler = False

    def set_session_started(self):
        self.session_started = True

    def update_client(self):
        self.update_client_layout()
        self.create_client_layers()



    def update_client_layout(self):
        ''' add here changes in the layout based on config reloads from server '''

        # TODO: I just inverted, putting set_text_style before set_stimuli_dimensions. Test this on other programs (market2, simple test, etc)
        # redo part of set_window: dimensions and styles, just don't redo draw_area
        self.set_text_styles()
        self.set_stimuli_dimensions()

    def ready(self):
        ''' the player is ready '''
        # show waiting message
        msg = MessageLayerStyled(my.net_msg['wait'],
                                 back_color=my.layout['color']['back wait'],
                                 rich_text=True)
        director.replace(Scene(msg))

        # tell server that client is ready
        self.callRemote(cmd.ClientReady)

    def custom_end_session(self, status):
        '''Placeholder for custom adjustments for end layer'''
        pass


class BAClientFactory(_InstanceFactory):
    '''Factory used by ClientCreator, using TwistedClient protocol.'''

    protocol = BAClient

    def __init__(self, reactor, instance, deferred):
        _InstanceFactory.__init__(self, reactor, instance, deferred)

    def __repr__(self):
        return "<BAClient factory: %r>" % (self.instance,)

def main():
    global c
    app.PrepareBase()
    # start the network client
    c = BAClient()

    # log stdout using twisted
    log.startLogging(sys.stdout)

    # Add connection scene to director
    start_scene = Scene(MessageLayerStyled('connecting...'))
    # TODO: add net_message

    director_run_no_loop(start_scene)

    if net_options.pyglet_reactor:
        @director.window.event
        def on_close():
            reactor.stop()

            # Return true to ensure that no other handlers
            # on the stack receive the on_close event
            return True
    else:
        task.coiterate(twisted_draw()\
                        ).addCallback(shutdown).addErrback(bailout)

    # create a factory, connect to server and store the protocol instance
    deferred = defer.Deferred()

    fac = BAClientFactory(reactor, c, deferred)

    def store_protocol(p):
        fac.p = p
        if net_options.observer:
            fac.p.callRemote(cmd.AddObserver
                                ).addErrback(bailout)
        else:
            fac.p.callRemote(cmd.AddClient).addErrback(bailout)

    HOST = my.network['host']
    PORT = my.network['port']
    connector = reactor.connectTCP(HOST, PORT, fac) #@UnusedVariable
    deferred.addCallback(store_protocol)
    deferred.addErrback(lambda reason: schedule_once(c.cant_connect, 2,
                                                str(reason.value)))
    # start network_loop
    reactor.run(call_interval=1 / 100.)

c = None # client protocol (or controller)

if __name__ == '__main__':
    import traceback
    try:
        main()
    finally:
        traceback.print_exc(file=sys.stderr)
        if options.use_log:
            my.stout.close()
